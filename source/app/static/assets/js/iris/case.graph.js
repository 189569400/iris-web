
function get_case_graph() {

    $.ajax({
        url: 'graph/getdata' + case_param(),
        type: "GET",
        dataType: "json",
        success: function (data) {
            if (data.status == 'success') {
                redrawAll(data.data);
                hide_loader();
            } else {
                $('#submit_new_asset').text('Save again');
                swal("Oh no !", data.message, "error")
            }
        },
        error: function (error) {
            $('#submit_new_asset').text('Save');
            swal("Oh no !", error.statusText, "error")
        }
    });

}

var network;

function redrawAll(data) {
  var container = document.getElementById("graph-container");
  var options = {
    edges: {
      smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.5
        }
    },
    layout: {
        randomSeed: 2,
        improvedLayout: true
    },
    interaction: {
      hideEdgesOnDrag: false
    },
    width: (window.innerWidth - 400) + "px",
    height: (window.innerHeight- 250) + "px",
    "physics": {
    "forceAtlas2Based": {
      "gravitationalConstant": -167,
      "centralGravity": 0.04,
      "springLength": 0,
      "springConstant": 0.02,
      "damping": 0.9
    },
    "minVelocity": 0.41,
    "solver": "forceAtlas2Based",
    "timestep": 0.45
    },
    groups: {
        computer: {
            shape: 'icon',
            icon: {
              face: "'Font Awesome 5 Solid'",
              weight: "bold", // Font Awesome 5 doesn't work properly unless bold.
              code: '\uf109'
            }
        },
        account: {
            shape: 'icon',
            icon: {
              face: "'Font Awesome 5 Solid'",
              weight: "bold", // Font Awesome 5 doesn't work properly unless bold.
              code: '\uf007'
            }
        }
    }
  };

  nodes = data.nodes;
  edges = data.edges;

  network = new vis.Network(container, data, options);

  network.on("stabilizationIterationsDone", function () {
        network.setOptions( { physics: false } );
    });

}


/* Page is ready, fetch the assets of the case */
$(document).ready(function(){
    get_case_graph();
});

