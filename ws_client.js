document.addEventListener('DOMContentLoaded',function(){
    const websocketClient = new WebSocket("ws://localhost:8080/");

    websocketClient.onopen = function(){
        console.log("Client connected");
        websocketClient.send("hello")
    }

},false);