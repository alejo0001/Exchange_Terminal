let token = document.getElementById("token");
let temporalidad = document.getElementById("temporalidad");
let porcentaje = document.getElementById("porcentaje");
const socket = new WebSocket("ws://localhost:8765");
const select = document.querySelector('select'); 


let listaTokens =['1000BONKUSDT','ICPUSDT'];

listaTokens.forEach(i=>{let newOption = new Option(i,i);
    select.add(newOption,undefined);
    });

function cambiarToken(){
    let option=""
    option = select.selectedOptions[0].label;
    socket.send(option)
}

        // Conexión abierta
        socket.addEventListener("open", (event) => {
            // let input = document.getElementById("message_input");
            console.log("Conexión abierta");
            socket.send("cliente web conectado");
        });

        // Escucha mensajes del servidor
        socket.addEventListener("message", (event) => {
            let temporalidad = document.getElementById("temporalidad");
            let porcentaje = document.getElementById("porcentaje");

            if(event.data.includes("{")){
                let jresponse = event.data.split("Mensaje del servidor: ")[0];
                let response= JSON.parse(jresponse);
                porcentaje.innerHTML = response.percentage;
            }
            

            
            console.log(`Mensaje del servidor: ${event.data}`);
            temporalidad.innerHTML = event.data;
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