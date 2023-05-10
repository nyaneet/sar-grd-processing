import sys
sys.path.append('/home/bagurgle/.snap/snap-python')

import snappy
from snappy import Product
from snappy import ProductIO
from snappy import ProductUtils
from snappy import WKTReader
from snappy import HashMap
from snappy import GPF

def read_product(product_path) -> snappy.Product:
    return ProductIO.readProduct(product_path)

def apply_orbit_file(input_product) -> snappy.Product:
    parameters = HashMap()
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    
    parameters.put('orbitType', 'Sentinel Precise (Auto Download)')
    parameters.put('polyDegree', '3')
    parameters.put('continueOnFail', 'false')
    return GPF.createProduct(
        'Apply-Orbit-File',
        parameters,
        input_product,
    )

def remove_thermal_noise(input_product) -> snappy.Product:
    parameters = HashMap()
    parameters.put('removeThermalNoise', True)
    return GPF.createProduct(
        'ThermalNoiseRemoval',
        parameters,
        input_product,
    )

def remove_grd_border_noise(input_product) -> snappy.Product:
    parameters = HashMap()
    parameters.put('borderLimit', '500')
    parameters.put('trimThreshold', '0.5')
    return GPF.createProduct(
        'Remove-GRD-Border-Noise',
        parameters,
        input_product,
    )

def subset(input_product, wkt_aoi) -> snappy.Product:
    SubsetOp = snappy.jpy.get_type('org.esa.snap.core.gpf.common.SubsetOp')
    geometry = WKTReader().read(wkt_aoi)
    
    HashMap = snappy.jpy.get_type('java.util.HashMap')
    GPF.getDefaultInstance().getOperatorSpiRegistry().loadOperatorSpis()
    
    parameters = HashMap()
    parameters.put('copyMetadata', True)
    parameters.put('geoRegion', geometry)
    return GPF.createProduct('Subset', parameters, input_product)

def calibrate(input_product, polarization) -> snappy.Product:
    parameters = HashMap()
    parameters.put('outputSigmaBand', True)
    parameters.put('sourceBands', f'Intensity_{polarization}')
    parameters.put('selectedPolarisations', polarization)
    return GPF.createProduct('Calibration', parameters, input_product)

def speckle_filter(product, polarization) -> snappy.Product:
    parameters = HashMap()
    parameters.put('sourceBands', f'Sigma0_{polarization}')
    parameters.put('filter', 'Refined Lee')
    return GPF.createProduct('Speckle-Filter', parameters, product)

def scale_in_db(input_product) -> snappy.Product:
    parameters = HashMap()
    return GPF.createProduct('linearToFromdB', parameters, input_product)

def terrain_correction(input_product, polarization) -> snappy.Product:
    parameters = HashMap()
    parameters.put('demName', 'GETASSE30')
    parameters.put('imgResamplingMethod', 'BILINEAR_INTERPOLATION')
    parameters.put('sourceBands', f'Sigma0_{polarization}')
    parameters.put('saveProjectedLocalIncidenceAngle', True)
    parameters.put('saveSelectedSourceBand', True)
    return GPF.createProduct('Terrain-Correction', parameters, input_product)

def process_product(
    product_path,
    wkt_aoi,
    out_path,
    out_name,
    polarizations,
) -> None:
    product = read_product(product_path)
    
    if polarizations is None:
        polarizations = []
        bands = product.getBandNames()
        if 'Intensity_HH' in bands:
            polarizations.append('HH')
        if 'Intensity_HV' in bands:
            polarizations.append('HV')
        if 'Intensity_VV' in bands:
            polarizations.append('VV')
        if 'Intensity_VH' in bands:
            polarizations.append('VH')
        
    product = apply_orbit_file(product)
    product = remove_thermal_noise(product)
    product = remove_grd_border_noise(product)
    product = subset(product, wkt_aoi)
    for polarization in polarizations:
        product_pol = calibrate(product, polarization)
        product_pol = speckle_filter(product_pol, polarization)
        product_pol = terrain_correction(product_pol, polarization)
        product_pol = scale_in_db(product_pol)
        
        ProductIO.writeProduct(
            product_pol,
            f'{out_path}/{out_name}_{polarization}',
            'GeoTIFF',
        )

        del product_pol
    del product

import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    '--wkt_aoi',
    type=str,
    required=True,
)

parser.add_argument(
    '--product_path',
    type=str,
    required=True,
)

parser.add_argument(
    '--out_path',
    type=str,
    required=True,
)

parser.add_argument(
    '--out_name',
    type=str,
    required=True,
)

parser.add_argument(
    '--polarizations',
    type=str,
    required=False,
)

if __name__ == '__main__':
    args = parser.parse_args()
    process_product(args.product_path, args.wkt_aoi, args.out_path, args.out_name, args.polarizations) 
