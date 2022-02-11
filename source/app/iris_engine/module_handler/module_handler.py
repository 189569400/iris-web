#!/usr/bin/env python3
#
#  IRIS Source Code
#  Copyright (C) 2021 - Airbus CyberSecurity (SAS)
#  ir@cyberactionlab.net
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
import base64
import logging

import importlib
from flask_login import current_user

from pickle import loads, dumps

from app import app, db, celery

from app.datamgmt.iris_engine.modules_db import iris_module_exists, iris_module_add, modules_list_pipelines, \
     get_module_config_from_hname
from app.models import IrisHook, IrisModuleHook, IrisModule
from iris_interface import IrisInterfaceStatus as IStatus

log = logging.getLogger(__name__)

def check_module_compatibility(module_version):
    return True


def check_pipeline_args(pipelines_args):
    """
    Verify that the pipeline arguments are correct and can be used later on
    :param pipelines_args: JSON pipelines
    :return: Status
    """
    logs = []
    has_error = False

    if type(pipelines_args) != dict:
        return True, ["Error - Pipeline args are not json"]

    if not pipelines_args.get("pipeline_internal_name"):
        has_error = True
        logs.append("Error - pipeline_internal_name missing from pipeline config")

    if not pipelines_args.get("pipeline_human_name"):
        has_error = True
        logs.append("Error - pipeline_human_name missing from pipeline config")

    if not pipelines_args.get("pipeline_args"):
        has_error = True
        logs.append("Error - pipeline_args missing from pipeline config")

    if not pipelines_args.get("pipeline_update_support"):
        has_error = True
        logs.append("Error - pipeline_update_support missing from pipeline config")

    if not pipelines_args.get("pipeline_import_support"):
        has_error = True
        logs.append("Error - pipeline_import_support missing from pipeline config")

    return has_error, logs


def check_module_health(module_instance):
    """
    Returns a status on the health of the module.
    A non healthy module will not be imported
    :param module_instance: Instance of the module to check
    :return: Status
    """
    logs = []

    def dup_logs(message):
        logs.append(message)
        log.info(message)

    if not module_instance:
        return False, ['Error - cannot instantiate the module. Check server logs']

    try:
        dup_logs("Testing module")
        dup_logs("Module name : {}".format(module_instance.get_module_name()))

        if not (float(app.config.get('MODULES_INTERFACE_MIN_VERSION'))
                <= module_instance.get_interface_version()
                <= float(app.config.get('MODULES_INTERFACE_MAX_VERSION'))):
            log.critical("Module interface no compatible with server. Expected "
                         f"{app.config.get('MODULES_INTERFACE_MIN_VERSION')} <= module "
                         f"<= {app.config.get('MODULES_INTERFACE_MAX_VERSION')}")
            logs.append("Module interface no compatible with server. Expected "
                        f"{app.config.get('MODULES_INTERFACE_MIN_VERSION')} <= module "
                        f"<= {app.config.get('MODULES_INTERFACE_MAX_VERSION')}")

            return False, logs

        dup_logs("Module interface version : {}".format(module_instance.get_interface_version()))

        module_type = module_instance.get_module_type()
        if module_type not in ["module_pipeline", "module_processor"]:
            log.critical(f"Unrecognised module type. Expected module_pipeline or module_processor, got {module_type}")
            logs.append(f"Unrecognised module type. Expected module_pipeline or module_processor, got {module_type}")
            return False, logs

        dup_logs("Module type : {}".format(module_instance.get_module_type()))

        if not module_instance.is_providing_pipeline() and module_type == 'pipeline':
            log.critical("Module of type pipeline has no pipelines")
            logs.append("Error - Module of type pipeline has not pipelines")
            return False, logs

        if module_instance.is_providing_pipeline():
            dup_logs("Module has pipeline : {}".format(module_instance.is_providing_pipeline()))
            # Check the pipelines config health
            has_error, llogs = check_pipeline_args(module_instance.pipeline_get_info())

            logs.extend(llogs)

            if has_error:
                return False, logs

        dup_logs("Module health validated")
        return module_instance.is_ready(), logs

    except Exception as e:
        log.error(e.__str__())
        logs.append(e.__str__())
        return False, logs


def instantiate_module_from_name(module_name):
    """
    Instantiate a module from a name. The method is not Exception protected.
    Caller need to take care of it failing.
    :param module_name: Name of the module to register
    :return: Class instance or None
    """
    mod_root_interface = importlib.import_module(module_name)
    if not mod_root_interface:
        return None

    # The whole concept is based on the fact that the root module provides an __iris_module_interface
    # variable pointing to the interface class with which Iris can talk to
    mod_interface = importlib.import_module("{}.{}".format(module_name,
                                                           mod_root_interface.__iris_module_interface))
    if not mod_interface:
        return None

    # Now get a handle on the interface class
    cl_interface = getattr(mod_interface, mod_root_interface.__iris_module_interface)
    if not cl_interface:
        return None

    # Try to instantiate the class
    mod_inst = cl_interface()

    return mod_inst


def configure_module_on_init(module_instance):
    """
    Configure a module after instantiation, with the current configuration
    :param module_instance: Instance of the module
    :return: IrisInterfaceStatus
    """
    if not module_instance:
        return IStatus.I2InterfaceNotImplemented('Module not found')

    return IStatus.I2ConfigureSuccess


def preset_init_mod_config(mod_config):
    """
    Prefill the configuration with default one
    :param mod_config: Configuration
    :return: Tuple
    """
    index = 0
    for config in mod_config:

        if config.get('default') is not None:
            mod_config[index]["value"] = config.get('default')
        index += 1

    return mod_config


def get_mod_config_by_name(module_name):
    """
    Returns a module configurationn based on its name
    :param: module_name: Name of the module
    :return: IrisInterfaceStatus
    """
    data = get_module_config_from_hname(module_name)

    if not data:
        return IStatus.I2InterfaceNotReady(message="Module not registered")

    return IStatus.I2Success(data=data)


def register_module(module_name):
    """
    Register a module into IRIS
    :param module_name: Name of the module to register
    """

    if not module_name:
        log.error("Provided module has no names")
        return False, ["Module has no names"]

    try:

        mod_inst = instantiate_module_from_name(module_name=module_name)
        if not mod_inst:
            log.error("Module could not be instantiated")
            return False, ["Module could not be instantiated"]

        if iris_module_exists(module_name=module_name):
            log.error("Module already exists in Iris")
            return False, ["Module already exists in Iris"]

        # Auto parse the configuration and fill with default
        mod_config = preset_init_mod_config(mod_inst.get_init_configuration())

        modu_id = iris_module_add(module_name=module_name,
                                  module_human_name=mod_inst.get_module_name(),
                                  module_description=mod_inst.get_module_description(),
                                  module_config=mod_config,
                                  module_version=mod_inst.get_module_version(),
                                  interface_version=mod_inst.get_module_version(),
                                  has_pipeline=mod_inst.is_providing_pipeline(),
                                  pipeline_args=mod_inst.pipeline_get_info(),
                                  module_type=mod_inst.get_module_type()
                                  )

        if not modu_id:
            return False, ["Unable to register module"]

        if mod_inst.get_module_type() == 'module_processor':
            mod_inst.register_hooks(module_id=modu_id)

    except Exception as e:
        return False, ["Fatal - {}".format(e.__str__())]

    return True, ["Module registered"]


def register_hook(module_id: int, iris_hook_name: str, manual_hook_name: str = None,
                  run_asynchronously: bool = True):
    """
    Register a new hook into IRIS. The hook_name should be a well-known hook to IRIS. iris_hooks table can be
    queried, or by default they are declared in iris source code > source > app > post_init.

    If is_manual_hook is set, the hook is triggered by user action and not automatically. If set, the iris_hook_name
    should be a manual hook (aka begin with on_manual_trigger_) otherwise an error is raised.

    If run_asynchronously is set (default), the action will be sent to RabbitMQ and processed asynchronously.
    If set to false, the action is immediately done, which means it needs to be quick otherwise the request will be
    pending and user experience degraded.

    :param module_id: Module ID to register
    :param iris_hook_name: Well-known hook name to register to
    :param manual_hook_name: The name of the hook displayed in the UI, if is_manual_hook is set
    :param run_asynchronously: Set to true to queue the module action in rabbitmq
    :return: Tuple
    """

    module = IrisModule.query.filter(IrisModule.id == module_id).first()
    if not module:
        return False, [f'Module ID {module_id} not found']

    is_manual_hook = False
    if "on_manual_trigger_" in iris_hook_name:
        is_manual_hook = True
        if not manual_hook_name:
            # Set default hook name
            manual_hook_name = f"{module.module_name}::{iris_hook_name}"

    hook = IrisHook.query.filter(IrisHook.hook_name == iris_hook_name).first()
    if not hook:
        return False, [f"Hook {iris_hook_name} is unknown"]

    if not isinstance(is_manual_hook, bool):
        return False, [f"Expected bool for is_manual_hook but got {type(is_manual_hook)}"]

    if not isinstance(run_asynchronously, bool):
        return False, [f"Expected bool for run_asynchronously but got {type(run_asynchronously)}"]

    imh = IrisModuleHook()
    imh.is_manual_hook = is_manual_hook
    imh.wait_till_return = False
    imh.run_asynchronously = run_asynchronously
    imh.max_retry = 0
    imh.manual_hook_ui_name = manual_hook_name if manual_hook_name else ""
    imh.hook_id = hook.id
    imh.module_id = module_id

    try:
        db.session.add(imh)
    except Exception as e:
        return False, [str(e)]

    return True, [f"Hook {iris_hook_name} registered"]


@celery.task(bind=True)
def task_hook_wrapper(self, module_name, hook_name, data, init_user, caseid):
    """
    Wrap a hook call into a Celery task to run asynchronously

    :param self: Task instance
    :param module_name: Module name to instanciate and call
    :param hook_name: Name of the hook which was triggered
    :param data: Data associated to the hook to process
    :param init_user: User initiating the task
    :param caseid: Case associated
    :return: A task status JSON task_success or task_failure
    """
    # Data is serialized, so deserialized
    deser_data = loads(data=base64.b64decode(data))

    # The receive object will most likely be cleared when handled by the task,
    # so we need to attach it to a the session in the task
    obj = db.session.merge(deser_data)
    db.session.commit()

    log.info(f'Calling module {module_name} for hook {hook_name}')

    try:
        mod_inst = instantiate_module_from_name(module_name=module_name)

        mod_inst.set_log_handler()
        task_status = mod_inst.hooks_handler(hook_name, data=obj)

        # Recommit the changes made by the module
        db.session.commit()

    except Exception as e:
        msg = f"Failed to run hook {hook_name} with module {module_name}. Error {str(e)}"
        log.critical(msg)
        print(msg)
        task_status = IStatus.I2Error(message=msg)

    return task_status


def call_modules_hook(hook_name: str, data: any, caseid: int) -> any:
    """
    Calls modules which have registered the specified hook

    :raises: Exception if hook name doesn't exist. This shouldn't happen
    :param hook_name: Name of the hook to call
    :param data: Data associated with the hook
    :param caseid: Case ID
    :return: Any
    """
    hook = IrisHook.query.filter(IrisHook.hook_name == hook_name).first()
    if not hook:
        log.critical(f'Hook name {hook_name} not found')
        raise Exception(f'Hook name {hook_name} not found')

    modules = IrisModuleHook.query.with_entities(
        IrisModuleHook.run_asynchronously,
        IrisModule.module_name
    ).filter(
        IrisModule.is_active == True,
        IrisModuleHook.hook_id == hook.id
    ).join(
        IrisModuleHook.module,
        IrisModuleHook.hook
    ).all()

    for module in modules:
        if module.run_asynchronously and "on_preload_" not in hook_name:
            # We cannot directly pass the sqlalchemy in data, as it needs to be serializable
            # So pass a dumped instance and then rebuild on the task side
            ser_data = base64.b64encode(dumps(data)).decode('utf8')
            task_hook_wrapper.delay(module_name=module.module_name, hook_name=hook_name, data=ser_data,
                                    init_user=current_user.name, caseid=caseid)

        else:
            # Direct call. Should be fast
            log.info(f'Calling module {module.module_name} for hook {hook_name}')

            try:

                mod_inst = instantiate_module_from_name(module_name=module.module_name)
                status = mod_inst.hooks_handler(hook_name, data=data)

            except Exception as e:
                log.critical(f"Failed to run hook {hook_name} with module {module.module_name}. Error {str(e)}")
                continue

            if status.is_success():
                data = status.get_data()

    return data


def list_available_pipelines():
    """
    Return a list of available pipelines by requesting the DB
    """
    data = modules_list_pipelines()

    return data
