import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
//import Highcharts from 'highcharts';
//import * as Highcharts from 'highcharts-angular';
import * as Highcharts from 'highcharts/highstock';
import { HighchartsChartModule } from 'highcharts-angular';
import { HttpClientModule } from '@angular/common/http';
import { FormBuilder, FormGroup, Validators,ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ITemporality } from './dtos/temporality.dto';
import { IPriceActionCalibrationDto } from './dtos/price-action-calibration.dto';
import { IPriceGroup } from './dtos/api-dtos.dto';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [HighchartsChartModule,HttpClientModule,ReactiveFormsModule,CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css'
})
export class AppComponent {
  title = 'exchange_terminal';
  Highcharts: typeof Highcharts = Highcharts;
  updateFlag = false;
  chartOptions?: Highcharts.Options;
  calibrationForm: FormGroup;

  lstTemporalities: ITemporality[] = [
    {text:'1m',value:'1'},
    {text:'3m',value:'3'},
    {text:'5m',value:'5'},
    {text:'15m',value:'15'},
    {text:'1h',value:'60'},
    {text:'4h',value:'240'},
    {text:'1d',value:'D'}]

  //apiUrl = 'https://api-testnet.bybit.com/v5/market/kline?category=linear&symbol=1000TURBOUSDT&interval=15&limit=200';
  //apiUrl = 'https://api.bybit.com/v5/market/kline?category=linear&symbol=1000TURBOUSDT&interval=15&limit=200';
  apiUrl = 'https://api.bybit.com/v5/market/kline';
  apiKey = '';
  apiSecret = '';
  
  headers = new HttpHeaders({
    'api-key': this.apiKey,
    'api-signature': this.apiSecret,
  });

  params = {
    category: 'linear',
    symbol: '1000TURBOUSDT',
    interval: '15',
    limit: '200',
  };
  constructor(
    private http: HttpClient,
    private fb: FormBuilder,
    
  ) { 

    this.calibrationForm = this.fb.group({
      rangeDivisor: [null, [Validators.required, Validators.required]],
      precision: [null, [Validators.required, Validators.required]],
      temporality: ['', Validators.required],
      minBouncesAmount :[null,Validators.required]
    });
  }

  ngOnInit(): void {
    this.fetchKlinesData();
  }
  fetchKlinesData(): void {
    const options = {
      headers : this.headers,
      params: this.params
    }
    this.http.get(this.apiUrl,options).subscribe((data: any) => {
      console.log(data)
      let ohlc = data.result.list.map((kline:any) => [
        //kline.open_time * 1000, // convertir a milisegundos
        parseFloat(kline[1]),
        parseFloat(kline[2]),
        parseFloat(kline[3]),
        parseFloat(kline[4])
      ]);
      ohlc.reverse();
      console.log('ohlc: ',ohlc)
      this.chartOptions = {
        rangeSelector: {
          selected: 1
        },
        title: {
          text: '1000TURBOUSDT OHLC'
        },
        yAxis: {
          plotBands: [{ // Resistencia
            from: 4.45, // Valor desde donde empieza la franja
            to: 4.47, // Valor hasta donde llega la franja
            color: 'rgba(255, 0, 0, 0.2)', // Color rojo con 20% de opacidad
            label: {
              text: 'Resistencia',
              style: {
                color: '#606060'
              }
            }
          }, { // Soporte
            from: 4.36,
            to: 4.38,
            color: 'rgba(0, 255, 0, 0.2)', // Color verde con 20% de opacidad
            label: {
              text: 'Soporte',
              style: {
                color: '#606060'
              }
            }
          }]
        },
        series: [{
          type: 'candlestick',
          name: '1000TURBOUSDT',
          data: ohlc,
          upColor: 'green', // Color de las velas con cierre mayor al de apertura
          color: 'red',     // Color de las velas con cierre menor al de apertura
          upLineColor: 'green', // Color del borde de las velas con cierre mayor al de apertura
          lineColor: 'red',     // Color del borde de las velas con cierre menor al de apertura
          lineWidth: 1, // Ancho del borde de las velas
          tooltip: {
            valueDecimals: 4
          }
        }],
        chart: {
          type: 'stockChart',
          zooming: {
            type: 'x' // Enable zoom on x-axis
          },
          backgroundColor: '#101014'
        },
        scrollbar: {
          enabled: true // Habilita la barra de desplazamiento
        }
      };
      this.updateFlag = true;
    })
  }

  calibrar() {
    if (this.calibrationForm!.valid) {
      const datos = this.calibrationForm!.value;
      let plotBands : Highcharts.YAxisPlotBandsOptions[] = []

      // headers = new HttpHeaders({
      //   'api-key': this.apiKey,
      // });
    
      this.http.post('http://127.0.0.1:8000/priceActionCalibration',datos as IPriceActionCalibrationDto).subscribe(data=>{
        console.log(data);
        let result = data as IPriceGroup[]
        result.forEach(element => {
          let plotBand ={  from: element.minPrice, // Valor desde donde empieza la franja
            to: element.maxPrice, // Valor hasta donde llega la franja
            color: 'rgba(0, 0, 255, 0.2)', // Color rojo con 20% de opacidad
          }
          plotBands.push(plotBand)
        });

        this.chartOptions!.yAxis! = {plotBands : plotBands}
        this.updateFlag = true
        console.log('plotBands: ',plotBands)
      })
      // Aquí puedes enviar los datos a tu API
      console.log('Datos enviados:', datos);
    } else {
      console.log('Formulario inválido. Verifica los campos.');
    }
  }
}


