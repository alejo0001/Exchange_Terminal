import { MarketZonesResponse } from "./api-dtos.dto";

export interface ISelectList{
    value: string;
    text : string;
}

export interface IPlot{
    temporality:string;
    dataResponse: MarketZonesResponse
}