import pandas as pd
import numpy as np
import asf_search as asf
import json

IIP_DATASET_PATH = 'IIP-dataset'
IIP_BY_YEARS = {
    '2021': 'IIP_2021IcebergSeason.csv',
    '2020': 'IIP_2020IcebergSeason.csv',
    '2019': 'IIP_2019IcebergSeason.csv',
}

PROCESSING_YEAR = 2019


def get_iip_filepath(year: int) -> str:
    return f'{IIP_DATASET_PATH}/{IIP_BY_YEARS[str(year)]}'

def search_sar_snapshot(
    wkt_aoi: str,
    start: datetime, 
    end: datetime,
    result_processor: Callable[[asf.ASFProduct], asf.ASFProduct] = None,
    platform: str = asf.PLATFORM.SENTINEL1,
) -> list[asf.ASFProduct]:
    opts = {
        'platform': platform,
        'start': start,
        'end': end,
    }
    
    results = asf.geo_search(intersectsWith=wkt_aoi, **opts) 
    if result_processor is None:
        return results
    
    for result in results:
        result_processor(result)
    
    global total_snapshots
    global total_unique_snapshots
    
    total_snapshots += len(results)
    total_unique_snapshots += 1 if len(results) > 0 else 0
    
    return results

def add_search_result(
    product: asf.ASFProduct,
    iceberg_info: dict,
    urls: dict=download_urls,
    results: dict=search_results,
) -> asf.ASFProduct:
    iceberg_id = '{}_{}_{}'.format(
        iceberg_info['ICEBERG_YEAR'],
        iceberg_info['ICEBERG_CSV_IDX'],
        iceberg_info['ICEBERG_NUMBER'],
    )
    
    product_info = product.geojson()
    product_url = product_info['properties']['url']
    
    urls.setdefault(product_url, [])
    urls[product_url].append({
        'id': iceberg_id,
        'snapshot_info': product_info,
        'iceberg_info': iceberg_info,
    })
    
    results.setdefault(iceberg_id, [])
    results[iceberg_id].append({
        'snapshot_info': product_info,
        'iceberg_info': iceberg_info,
    })
    
    return product


if __name__ == '__main__':
    iip_data = pd.read_csv(filepath_or_buffer=get_iip_filepath(PROCESSING_YEAR))

    search_interval = timedelta(days=1)
    download_urls = {}
    search_results = {}

    total_snapshots = 0
    total_unique_snapshots = 0

    progress_bar = tqdm(
    iip_data.iterrows(),
    total=iip_data.shape[0],
    desc='',
    )

    for idx, iceberg_data in progress_bar:
        iceberg_info = iceberg_data.to_dict()
        iceberg_info['ICEBERG_CSV_IDX'] = idx
        
        sighting_date = datetime.strptime(iceberg_data['SIGHTING_DATE'], '%m/%d/%Y')
        
        lon, lat = iceberg_data['SIGHTING_LONGITUDE'], iceberg_data['SIGHTING_LATITUDE']
        wkt_aoi = f'POINT({lon} {lat})'
        
        results = search_sar_snapshot(
            wkt_aoi=wkt_aoi,
            start=sighting_date,
            end=sighting_date+search_interval,
            result_processor=lambda res: add_search_result(product=res, iceberg_info=iceberg_info),
        )
        
        progress_bar.set_description(
            'Total: {:5d} | Unique: {:4d}'.format(
                total_snapshots, total_unique_snapshots
            )
        )

    with open(f'iip-urls-{PROCESSING_YEAR}.json', 'w') as out:
        json.dump(download_urls, out)
    
    with open(f'iip-search-result-{PROCESSING_YEAR}.json', 'w') as out:
        json.dump(search_results, out)
