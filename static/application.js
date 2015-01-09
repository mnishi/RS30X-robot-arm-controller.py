var ws = new WebSocket("ws://" + location.host + "/ws");

ws.onmessage = function(message){
    var data = JSON.parse(message.data);
    if('status' == data.msg_type){
        show_status(data.status);
    }
};

ws.onopen = function(){
    ws.send(JSON.stringify({msg_type: "status"}));
};

$(document).ready(function(){
    $("#Volume").buttonset();
    $("#Volume_Medium").prop("checked", true);
    $("#Volume").buttonset("refresh");
    
    $("#Pose_PX_Dec").button(); 
    $("#Pose_PY_Dec").button();
    $("#Pose_PZ_Dec").button();
    $("#Pose_RX_Dec").button();
    $("#Pose_RY_Dec").button();
    $("#Pose_RZ_Dec").button();
    $("#Pose_PX_Inc").button();
    $("#Pose_PY_Inc").button();
    $("#Pose_PZ_Inc").button();
    $("#Pose_RX_Inc").button();
    $("#Pose_RY_Inc").button();
    $("#Pose_RZ_Inc").button();
    $("#Joint_J1_Dec").button(); 
    $("#Joint_J2_Dec").button();
    $("#Joint_J3_Dec").button();
    $("#Joint_J4_Dec").button();
    $("#Joint_J5_Dec").button();
    $("#Joint_J6_Dec").button();
    $("#Joint_J1_Inc").button();
    $("#Joint_J2_Inc").button();
    $("#Joint_J3_Inc").button();
    $("#Joint_J4_Inc").button();
    $("#Joint_J5_Inc").button();
    $("#Joint_J6_Inc").button();
    
    $("#Pose_PX_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "px", direction: "dec", volume: $("#Volume :radio:checked").val()}))}); 
    $("#Pose_PY_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "py", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_PZ_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "pz", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RX_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rx", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RY_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "ry", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RZ_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rz", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_PX_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "px", direction: "inc", volume: $("#Volume :radio:checked").val()}))}); 
    $("#Pose_PY_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "py", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_PZ_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "pz", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RX_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rx", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RY_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "ry", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Pose_RZ_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rz", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J1_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "dec", volume: $("#Volume :radio:checked").val()}))}); 
    $("#Joint_J2_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J3_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J4_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J5_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J6_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "dec", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J1_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "inc", volume: $("#Volume :radio:checked").val()}))}); 
    $("#Joint_J2_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J3_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J4_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J5_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        
    $("#Joint_J6_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "inc", volume: $("#Volume :radio:checked").val()}))});        

});

function toFixed(num){
    return num.toFixed(3)
}

var stat
var stat_initialized = false
function show_status(s){
    stat = s

    if(stat_initialized == false){
        threeStart();
        stat_initialized = true
    }

    $("#Pose_PX").val(toFixed(s.pose[0]));    
    $("#Pose_PY").val(toFixed(s.pose[1]));    
    $("#Pose_PZ").val(toFixed(s.pose[2]));    
    $("#Pose_RX").val(toFixed(s.pose[3]));    
    $("#Pose_RY").val(toFixed(s.pose[4]));    
    $("#Pose_RZ").val(toFixed(s.pose[5]));    

    $("#Joint_J1").val(toFixed(s.joint[0]));    
    $("#Joint_J2").val(toFixed(s.joint[1]));    
    $("#Joint_J3").val(toFixed(s.joint[2]));    
    $("#Joint_J4").val(toFixed(s.joint[3]));    
    $("#Joint_J5").val(toFixed(s.joint[4]));    
    $("#Joint_J6").val(toFixed(s.joint[5]));    
}

var width, height;
var renderer;
function initThree() {
    width = $("#Canvas").prop('clientWidth');
    height = $("#Canvas").prop('clientHeight');
    renderer = new THREE.WebGLRenderer({antialias: true});
    renderer.setSize(width, height );
    $("#Canvas").append(renderer.domElement); 
    renderer.setClearColor(0xFFFFFF, 1.0);
}

var camera;
function initCamera() { 
    camera = new THREE.PerspectiveCamera( 45 , width / height , 1 , 1000 );
    camera.position.x = 150;
    camera.position.y = 100;
    camera.position.z = 100;
    camera.up.x = 0;
    camera.up.y = 0;
    camera.up.z = 1;
    camera.lookAt( {x:0, y:0, z:0 } );
}

var scene;
function initScene() {   
    scene = new THREE.Scene();
}

var light;
function initLight() { 
    light = new THREE.DirectionalLight(0xFFFFFF, 1.0, 0);
    light.position.set( 100, 100, 200 );
    scene.add(light);
    light2 = new THREE.AmbientLight(0x555555);
    scene.add(light2);    
}

var joint = new Array(8);
function initObject(){
    p = new THREE.Mesh(
            new THREE.PlaneGeometry(150, 150),               
            new THREE.MeshLambertMaterial({color: 0xBBBBBB, ambient: 0xBBBBBB})
            );
    scene.add(p);
    p.position.set(0,0,0);

    for(var i = 0; i < joint.length; i++){ 
        j = new THREE.Mesh(
                new THREE.BoxGeometry(5, 5, 2),               
                new THREE.MeshLambertMaterial({color: 0x6495ed, ambient: 0x6495ed})
                );
        scene.add(j);
        j.position.set(0,0,0);
        j.rotation.order = "ZYX";
        j.rotation.set(0,0,0);
        joint[i] = j
    }
}

function threeStart() {
    initThree();
    initCamera();
    initScene();   
    initLight();
    initObject();
    renderThree();
}

function renderThree() {
    joint[7].position.set(stat.pose[0], stat.pose[1], stat.pose[2]);
    joint[7].rotation.set(stat.pose[3] * Math.PI / 180, stat.pose[4] * Math.PI / 180, stat.pose[5] * Math.PI / 180);
    renderer.clear(); 
    renderer.render(scene, camera);
    window.requestAnimationFrame(renderThree);
}

