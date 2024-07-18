import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
//import Highcharts from 'highcharts';
//import * as Highcharts from 'highcharts-angular';
import * as Highcharts from 'highcharts/highstock';
import { HighchartsChartModule } from 'highcharts-angular';
import { HttpClientModule } from '@angular/common/http';
import { FormBuilder, FormGroup, Validators,ReactiveFormsModule  } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { IPlot, ISelectList } from './dtos/dtos.dto';
import { IPriceActionCalibrationDto } from './dtos/price-action-calibration.dto';
import { EntranceZonesResponse, IPriceGroup, MarketZonesResponse } from './dtos/api-dtos.dto';
import { IBybitTickersResponse, IBybitTickersResponseItem } from './dtos/bybit-tickers-response.dto';
import {temporalityColors}from './dtos/constants';
import { bybitApiKey, bybitApiSecret } from './config';
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
  tickerForm : FormGroup;
  plotBands : Highcharts.YAxisPlotBandsOptions[] = []
  lstPlots : IPlot[] = [];
  public globalPriceGroups : IPriceGroup[]=[]

  lstTemporalities: ISelectList[] = [
    {text:'1m',value:'1'},
    {text:'3m',value:'3'},
    {text:'5m',value:'5'},
    {text:'15m',value:'15'},
    {text:'1h',value:'60'},
    {text:'4h',value:'240'},
    {text:'1d',value:'D'}]

  lstCalculationMode : ISelectList[]=[
    {text:'Porcentaje',value:'0'},
    {text:'Divisor',value:'1'},
  ]


  lstTickers : IBybitTickersResponseItem[]=[]

  //apiUrl = 'https://api-testnet.bybit.com/v5/market/kline?category=linear&symbol=1000TURBOUSDT&interval=15&limit=200';
  //apiUrl = 'https://api.bybit.com/v5/market/kline?category=linear&symbol=1000TURBOUSDT&interval=15&limit=200';
  bybitApiDomain = 'https://api.bybit.com'
  apiDomain = 'http://127.0.0.1:8000'
  apiUrl = this.bybitApiDomain+'/v5/market/kline';
  urlTickers = this.bybitApiDomain+'/v5/market/tickers'
  apiKey = bybitApiKey
  apiSecret = bybitApiSecret
  
  
  headers = new HttpHeaders({
    'api-key': this.apiKey,
    'api-signature': this.apiSecret,
  });

 
 
  constructor(
    private http: HttpClient,
    private fb: FormBuilder,
    
  ) { 

    this.calibrationForm = this.fb.group({
      rangeDivisor: null,
      precision: null,
      temporality: ['', Validators.required],
      minBouncesAmount :[null,Validators.required],
      calculationMode : ['', Validators.required],
      percentage: null,   
      depth: null
    });

    this.tickerForm = this.fb.group({
      symbol:['']
    });
  }

  ngOnInit(): void {
    // this.fetchKlinesData();
    this.getTickers();
  }
  fetchKlinesData(): void {
    const  params = {
      category: 'linear',
      symbol: this.tickerForm.get('symbol')!.value,
      interval: this.calibrationForm.get('temporality')!.value != '' && this.calibrationForm.get('temporality')!.value != null? this.calibrationForm.get('temporality')!.value:'15',
      limit: '200',
    };
    const options = {
      headers : this.headers,
      params: params
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
          text: this.tickerForm.get('symbol')!.value
        },
        
        series: [{
          type: 'candlestick',
          name: this.tickerForm.get('symbol')!.value,
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
            type: 'xy' // Enable zoom on x-axis
          },
          // events: {
          //   load() {
          //     const chart = this;
      
          //     // Habilitar el panning con el mouse
          //     chart.container.addEventListener('mousedown', function (e: MouseEvent) {
          //       // Solo habilitar el panning con el botón izquierdo del mouse
          //       if (e.button !== 0) return;
      
          //       e.preventDefault();
          //       let isDragging = false;
          //       let startX = e.pageX;
          //       let startY = e.pageY;
          //       const chartX = chart.xAxis[0].toValue(startX);
          //       const chartY = chart.yAxis[0].toValue(startY);
      
          //       // Desactivar temporalmente el zooming durante el panning
          //       const originalZooming = chart.options.chart!.zooming;
          //       chart.update({ chart: { zooming: { type: undefined } } });
      
          //       function onMouseMove(e: MouseEvent) {
          //         isDragging = true;
          //         const newX = (chart.xAxis[0].toValue(e.pageX) - chartX) * 0.1; // Ajustar la sensibilidad
          //         const newY = (chart.yAxis[0].toValue(e.pageY) - chartY) * 0.1; // Ajustar la sensibilidad
          //         chart.xAxis[0].setExtremes(chart.xAxis[0].min! - newX, chart.xAxis[0].max! - newX, false);
          //         chart.yAxis[0].setExtremes(chart.yAxis[0].min! - newY, chart.yAxis[0].max! - newY, false);
          //         chart.redraw(false);
          //       }
      
          //       function onMouseUp() {
          //         if (isDragging) {
          //           document.removeEventListener('mousemove', onMouseMove);
          //           document.removeEventListener('mouseup', onMouseUp);
      
          //           // Restaurar la configuración de zooming después de terminar el panning
          //           chart.update({ chart: { zooming: originalZooming } });
          //         }
          //         isDragging = false;
          //       }
      
          //       document.addEventListener('mousemove', onMouseMove);
          //       document.addEventListener('mouseup', onMouseUp);
          //     });
          //   }
          // },
          panning: {
            enabled: true,
            type: 'xy' // Permite el panning en ambas direcciones: 'x', 'y' o 'xy'
          },
          //zoomType: 'xy' // Permite el zoom en ambas direcciones
          backgroundColor: '#101014'
        },
        scrollbar: {
          enabled: true // Habilita la barra de desplazamiento
        }
      };
      this.updateFlag = true;
    })
    this.setTicker()
  }

  getTickers(): void {
    let requestData={
      category: 'linear'
    }
    const options = {
      headers : this.headers,
      params: requestData
    }
    this.http.get(this.urlTickers,options).subscribe((data: any) => {
      console.log(data)
      const response = new IBybitTickersResponse(data)
      this.lstTickers = response.result.list
      this.lstTickers.sort((a,b)=>parseFloat(b.price24hPcnt) - parseFloat(a.price24hPcnt))
      
    })
  }

  setTicker(){
    const symbol = this.tickerForm.get('symbol')!.value
   
    this.http.get(this.apiDomain+'/setTicker/'+symbol ).subscribe(data=>{
        console.log(data);
       
      })
  }

  calibrar() {
    if (this.calibrationForm!.valid) {
      
      const datos = this.calibrationForm!.value;
      if(datos.percentage > 0){
        datos.percentage = datos.percentage/100
        datos.calculationMode = parseInt(datos.calculationMode)
        datos.rangeDivisor = datos.rangeDivisor == null ? 0 :  datos.rangeDivisor
        datos.precision = datos.precision == null ? 0 :  datos.precision
      }
       

      // headers = new HttpHeaders({
      //   'api-key': this.apiKey,
      // });
    
      this.http.post(this.apiDomain+'/priceActionCalibration',datos as IPriceActionCalibrationDto).subscribe(data=>{
        console.log(data);
        // let result = data as IPriceGroup[]
        let plot : IPlot = {
          temporality : this.calibrationForm.get('temporality')!.value,
          dataResponse : new MarketZonesResponse(data)
        }
        if(this.lstPlots.length >0){
          // Verificar si ya existe un plot con la misma temporalidad y actualizarlo
          let index = this.lstPlots.findIndex(p => p.temporality === plot.temporality);
          if (index !== -1) {
            this.lstPlots[index] = plot;
          } else {
            this.lstPlots.push(plot);
          }
          
         
        }
        else{
          this.lstPlots.push(plot)  
        }
        this.plotBands = []
        this.globalPriceGroups = []
        // this.chartOptions!.yAxis! = {plotBands : this.plotBands}
        // this.updateFlag = true
        this.lstPlots.forEach(element => {
          element.dataResponse.zones?.forEach(z=>{
            let plotBand ={  
              from: z.minPrice, // Valor desde donde empieza la franja
              to: z.maxPrice, // Valor hasta donde llega la franja
              color:  temporalityColors[element.temporality],
            }
            this.plotBands.push(plotBand)
            this.globalPriceGroups.push(z)
          })
         
        });

        this.chartOptions!.yAxis! = {plotBands : this.plotBands}
        this.updateFlag = true
        console.log('plotBands: ',this.plotBands)
        console.log('lstPlots: ',this.lstPlots)
      })
      // Aquí puedes enviar los datos a tu API
      console.log('Datos enviados:', datos);
    } else {
      console.log('Formulario inválido. Verifica los campos.');
    }
  }

  getEntranceZones(){
    const pGroups : IPriceGroup[]= this.sortPriceGroups(this.globalPriceGroups)  
    
    this.http.post(this.apiDomain+'/getEntranceZones',pGroups ).subscribe(data=>{
      this.plotBands = []
      const entranceZones : EntranceZonesResponse = new EntranceZonesResponse(data)
      this.lstPlots.forEach(element => {
        element.dataResponse.zones?.forEach(z=>{
          let plotBand ={  
            from: z.minPrice, // Valor desde donde empieza la franja
            to: z.maxPrice, // Valor hasta donde llega la franja
            color:  temporalityColors[element.temporality],
          }
          this.plotBands.push(plotBand)
        })
       
      });

      
      entranceZones.zones?.forEach(z=>{
          let plotBand ={  
            from: z.minPrice, // Valor desde donde empieza la franja
            to: z.maxPrice, // Valor hasta donde llega la franja
            color:  z.zoneType == 0 ? 'rgba(0,51,42,0.7)' : 'rgba(178,40,51,0.7)',
          }
          this.plotBands.push(plotBand)
        })
       
      this.chartOptions!.yAxis! = {plotBands : this.plotBands}
      this.updateFlag = true

    })
  }

  sortPriceGroups(priceGroups: IPriceGroup[]): IPriceGroup[] {
    // Ordenar la lista por minPrice
    priceGroups.sort((a, b) => a.minPrice - b.minPrice);
  
    // Crear una nueva lista para almacenar los resultados ordenados
    const sortedGroups: IPriceGroup[] = [];
  
    // Agregar el primer grupo a la lista ordenada
    if (priceGroups.length > 0) {
      sortedGroups.push(priceGroups[0]);
    }
  
    // Iterar a través de los grupos restantes y agregarlos si cumplen la condición
    for (let i = 1; i < priceGroups.length; i++) {
      const lastGroup = sortedGroups[sortedGroups.length - 1];
      const currentGroup = priceGroups[i];
  
      // Verificar si el minPrice del grupo actual es mayor que el maxPrice del último grupo en la lista ordenada
      if (currentGroup.minPrice > lastGroup.maxPrice) {
        sortedGroups.push(currentGroup);
      }
    }
  
    return sortedGroups;
  }
}


