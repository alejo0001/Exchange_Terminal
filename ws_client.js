document.addEventListener('DOMContentLoaded',function(){
    const websocketClient = new WebSocket("ws://localhost:8765/");

    websocketClient.onopen = function(){
        console.log("Client connected");
        websocketClient.send("hello")
    }

    // websocketClient.onmessage = function (event) {
    //     console.log("Mensaje recibido del servidor:", event.data);
    // };

    // websocketClient.onclose = function (event) {
    //     if (event.wasClean) {
    //         console.log(`Conexión cerrada limpiamente, código=${event.code}, razón=${event.reason}`);
    //     } else {
    //         console.error("Conexión rota"); // ejemplo: el servidor se detuvo
    //     }
    // };

    // websocketClient.onerror = function (error) {
    //     console.error("Error en la conexión WebSocket:", error.message);
    // };
},false);