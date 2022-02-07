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

from typing import List

from app import db
from app.persistence.exceptions.sql.ElementExceptions import ElementNotFoundException
from app.persistence.exceptions.sql.ElementExceptions import ElementInUseException
from app.common.models import Client
from app.common.schema.marshables import CustomerSchema

client_schema = CustomerSchema()


def get_client_list() -> List[Client]:
    client_list = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id')
    ).all()

    output = [c._asdict() for c in client_list]

    return output


def get_client(client_id: str) -> Client:
    client = Client.query.filter(Client.client_id == client_id).first()
    return client


def get_client_api(client_id: str) -> Client:
    client = Client.query.with_entities(
        Client.name.label('customer_name'),
        Client.client_id.label('customer_id')
    ).filter(Client.client_id == client_id).first()

    output = client._asdict()

    return output


def create_client(client_name: str) -> Client:
    client_data = {
        "customer_name": client_name
    }

    client = client_schema.load(client_data)

    db.session.add(client)
    db.session.commit()

    return client


def update_client(client_id: str, client_name: str) -> Client:
    # TODO: Possible reuse somewhere else ...
    client = get_client(client_id)

    if not client:
        raise ElementNotFoundException('No Customer found with this uuid.')

    invariant_properties = ['client_id']
    properties = list(filter(lambda x: x not in invariant_properties, Client.__table__.columns.keys()))

    updated_client_data = {
        "customer_name": client_name
    }

    updated_client = client_schema.load(updated_client_data)

    for key in properties:
        if getattr(client, key) != getattr(updated_client, key):
            setattr(client, key, getattr(updated_client, key))

    db.session.commit()

    return client


def delete_client(client_id: str) -> None:
    client = Client.query.filter(
        Client.client_id == client_id
    ).first()

    if not client:
        raise ElementNotFoundException('No Customer found with this uuid.')

    try:

        Client.query.filter(
            Client.client_id == client_id
        ).delete()
        db.session.commit()

    except Exception as e:
        raise ElementInUseException('A used customer cannot be deleted')


