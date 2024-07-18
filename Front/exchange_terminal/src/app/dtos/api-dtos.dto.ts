export interface IPriceGroup {
    rangeValue: number;
    prices: number[];
    minPrice: number;
    maxPrice: number;
    sellZone: IEntranceZone;
    buyZone: IEntranceZone;

   
}

export interface IEntranceZone  {
    minPrice: number;
    maxPrice: number;
    zoneType: number;
    priceGroup: IPriceGroup;

  
}

export class EntranceZonesResponse{
    zones? : IEntranceZone[] = []
    
    constructor(jsonData: any) {
        Object.assign(this.zones!, jsonData);
    }
}

export class MarketZonesResponse{
    zones? : IPriceGroup[] = []
    
    constructor(jsonData: any) {
        Object.assign(this.zones!, jsonData);
    }
}




