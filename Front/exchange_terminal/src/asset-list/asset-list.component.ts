import { Component, OnInit } from '@angular/core';
import { ApiService } from 'ruta/a/tu/api.service'; // Importa tu servicio de API

@Component({
  selector: 'app-asset-list',
  templateUrl: './asset-list.component.html',
  styleUrls: ['./asset-list.component.css']
})
export class AssetListComponent implements OnInit {
  assets: any[]; // Definir el arreglo de activos

  constructor(private apiService: ApiService) { }

  ngOnInit(): void {
    this.loadAssets(); // Llama a la función para cargar los activos al inicializar el componente
  }

  loadAssets(): void {
    // Llama al servicio de API para obtener la lista de activos
    this.apiService.getAssets().subscribe((response: any) => {
      this.assets = response.data; // Asigna la respuesta de la API a la variable de activos
    });
  }
}