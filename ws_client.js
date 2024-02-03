// document.addEventListener('DOMContentLoaded',function(){
//     const websocketClient = new WebSocket("ws://localhost:8080/");

//     websocketClient.onopen = function(){
//         console.log("Client connected");
//         websocketClient.send("hello")
//     }

//     // websocketClient.onmessage = function (event) {
//     //     console.log("Mensaje recibido del servidor:", event.data);
//     // };

//     // websocketClient.onclose = function (event) {
//     //     if (event.wasClean) {
//     //         console.log(`Conexión cerrada limpiamente, código=${event.code}, razón=${event.reason}`);
//     //     } else {
//     //         console.error("Conexión rota"); // ejemplo: el servidor se detuvo
//     //     }
//     // };

//     // websocketClient.onerror = function (error) {
//     //     console.error("Error en la conexión WebSocket:", error.message);
//     // };
// },false);
let token = document.getElementById("token");
let temporalidad = document.getElementById("temporalidad");
let porcentaje = document.getElementById("porcentaje");
const socket = new WebSocket("ws://localhost:8765");

        // Conexión abierta
        socket.addEventListener("open", (event) => {
            // let input = document.getElementById("message_input");
            console.log("Conexión abierta");
            socket.send("cliente web conectado");
        });

        // Escucha mensajes del servidor
        socket.addEventListener("message", (event) => {
            let token = document.getElementById("token");
            console.log(`Mensaje del servidor: ${event.data}`);
            token.innerHTML = event.data;
            //alert(`Mensaje del servidor: ${event.data}`)
        });

        // Maneja errores
        socket.addEventListener("error", (event) => {
            console.error("Error en la conexión:", event);
        });

        // Conexión cerrada
        socket.addEventListener("close", (event) => {
            console.log("Conexión cerrada");
        });