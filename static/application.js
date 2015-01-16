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

    $("#Interpolation").buttonset();
    $("#Interpolation_line").prop("checked", true);
    $("#Interpolation").buttonset("refresh");
     
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
    
    $("#Pose_PX_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "px", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))}); 
    $("#Pose_PY_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "py", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_PZ_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "pz", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RX_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rx", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RY_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "ry", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RZ_Dec").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rz", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_PX_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "px", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))}); 
    $("#Pose_PY_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "py", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_PZ_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "pz", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RX_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rx", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RY_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "ry", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Pose_RZ_Inc").click( function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose",  target: "rz", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J1_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))}); 
    $("#Joint_J2_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J3_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J4_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J5_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J6_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "dec", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J1_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))}); 
    $("#Joint_J2_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J3_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J4_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J5_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        
    $("#Joint_J6_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "inc", volume: $("#Volume :radio:checked").val(), interpolate_type: $("#Interpolation :radio:checked").val()}))});        

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
    renderer.shadowMapEnabled = true;
    $("#Canvas").append(renderer.domElement); 
    renderer.setClearColor(0xFFFFFF, 1.0);
}

var camera;
function initCamera() { 
    camera = new THREE.PerspectiveCamera( 45 , width / height , 1 , 1000 );
    camera.position.x = 300;
    camera.position.y = 250;
    camera.position.z = 250;
    camera.up.x = 0;
    camera.up.y = 0;
    camera.up.z = 1;
    camera.lookAt( {x:0, y:0, z:100 } );
    var controls = new THREE.OrbitControls(camera);  
    controls.update(); 
}

var scene;
function initScene() {   
    scene = new THREE.Scene();
}

var light;
function initLight() { 
    light = new THREE.DirectionalLight(0xFFFFFF, 1.0, 0);
    light.position.set( 150, 150, 300 );
    light.castShadow = true;
    scene.add(light);
    light2 = new THREE.AmbientLight(0x555555);
    scene.add(light2);    
}

var joint = new Array(9);
function initObject(){
    p = new THREE.Mesh(
            new THREE.PlaneGeometry(400, 400),               
            new THREE.MeshLambertMaterial({color: 0xBBBBBB, ambient: 0xBBBBBB})
            );
    scene.add(p);
    p.position.set(0,0,0);
    p.receiveShadow = true;

    for(var i = 0; i < joint.length; i++){ 
        j = new THREE.Mesh(
                new THREE.BoxGeometry(10, 10, 3),               
                new THREE.MeshLambertMaterial({color: 0x6495ed, ambient: 0x6495ed})
                );
        scene.add(j);
        j.position.set(0,0,0);
        j.rotation.order = "ZYX";
        j.rotation.set(0,0,0);
        j.castShadow = true;
        j.Shadow = true;
        joint[i] = j
    }
}

var link = new Array(11);
function renderLink(initialize){
    lp = Array(1);
    lp[0] = [0, 0, 0, 0, 0, 0]
    lp = lp.concat(stat.link_pose)

    for(var i = 0; i < (link.length - 1); i++){
        if(initialize == true){
            if(i == 2 || i == 6){
                l = createLink(0, getLinkLength(lp[i], lp[i + 1]), 0);               
            }else if(i == 3 || i == 5){
                l = createLink(getLinkLength(lp[i], lp[i + 1]), 0, 0);               
            }else{
                l = new THREE.Mesh(
                        new THREE.BoxGeometry(2.5, 2.5, getLinkLength(lp[i], lp[i + 1])),               
                        new THREE.MeshLambertMaterial({color: 0x888888, ambient: 0x888888})
                        );
            }
            scene.add(l);
            l.castShadow = true;
            l.Shadow = true;
            l.rotation.order = "ZYX";
            link[i] = l
        }
        c = getLinkCenter(lp[i], lp[i + 1]);
        link[i].position.set(c[0], c[1],c[2]);
        link[i].rotation.set(lp[i][3], lp[i][4], lp[i][5]);
    }
}

function createLink(xoffset, yoffset, zoffset){
    return new THREE.Mesh(
            new THREE.BoxGeometry(2.5 + xoffset, 2.5 + yoffset, 2.5 + zoffset),               
            new THREE.MeshLambertMaterial({color: 0x888888, ambient: 0x888888})
            );
}

function getLinkLength(src, dest){
   return Math.pow(Math.pow(dest[0] - src[0], 2) + Math.pow(dest[1] - src[1], 2) + Math.pow(dest[2] - src[2], 2), 0.5)  
}

function getLinkCenter(src, dest){
    center = Array(3);
    center[0] = (dest[0] + src[0]) / 2;
    center[1] = (dest[1] + src[1]) / 2;
    center[2] = (dest[2] + src[2]) / 2;
    return center;
}

function threeStart() {
    initThree();
    initCamera();
    initScene();   
    initLight();
    initObject();
    renderLink(true);
    renderThree();
}

function renderThree() {
    for(var i = 1; i < joint.length; i++){
        joint[i].position.set(stat.joint_pose[i-1][0], stat.joint_pose[i-1][1], stat.joint_pose[i-1][2]);
        joint[i].rotation.set(stat.joint_pose[i-1][3], stat.joint_pose[i-1][4], stat.joint_pose[i-1][5]);
    }
    renderLink(false);
    renderer.clear(); 
    renderer.render(scene, camera);
    window.requestAnimationFrame(renderThree);
}

