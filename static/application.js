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
    $("#Pose_PX_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "px", direction: "dec"}))}); 
    $("#Pose_PY_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "py", direction: "dec"}))});        
    $("#Pose_PZ_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "pz", direction: "dec"}))});        
    $("#Pose_RX_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "rx", direction: "dec"}))});        
    $("#Pose_RY_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "ry", direction: "dec"}))});        
    $("#Pose_RZ_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "rz", direction: "dec"}))});        
    $("#Pose_PX_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "px", direction: "inc"}))}); 
    $("#Pose_PY_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "py", direction: "inc"}))});        
    $("#Pose_PZ_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "pz", direction: "inc"}))});        
    $("#Pose_RX_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "rx", direction: "inc"}))});        
    $("#Pose_RY_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "ry", direction: "inc"}))});        
    $("#Pose_RZ_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "pose", target: "rz", direction: "inc"}))});        
    $("#Joint_J1_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "dec"}))}); 
    $("#Joint_J2_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "dec"}))});        
    $("#Joint_J3_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "dec"}))});        
    $("#Joint_J4_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "dec"}))});        
    $("#Joint_J5_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "dec"}))});        
    $("#Joint_J6_Dec").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "dec"}))});        
    $("#Joint_J1_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j1", direction: "inc"}))}); 
    $("#Joint_J2_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j2", direction: "inc"}))});        
    $("#Joint_J3_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j3", direction: "inc"}))});        
    $("#Joint_J4_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j4", direction: "inc"}))});        
    $("#Joint_J5_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j5", direction: "inc"}))});        
    $("#Joint_J6_Inc").click(function(event){ws.send(JSON.stringify({msg_type: "jog", target_type: "joint", target: "j6", direction: "inc"}))});        
});

function toFixed(num){
    return num.toFixed(3)
}

function show_status(s){
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
