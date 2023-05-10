import unittest

from process_product import (
    read_product,
    apply_orbit_file,
    remove_thermal_noise,
    remove_grd_border_noise,
    subset,
    calibrate,
    speckle_filter,
    scale_in_db,
    terrain_correction,
)

class TestSnapshotProcessing(unittest.TestCase):
    def setUp(self):
        self.product_path = '/home/bagurgle/mag/iip/downloads/S1B_IW_GRDH_1SDH_20210614T100344_20210614T100409_027351_03443D_13A1.zip'
        self.wkt_aoi = 'POLYGON ((-58.75306600000002 55.02842699999997, -58.75306600000002 54.978426999999975, -58.803066000000015 54.978426999999975, -58.803066000000015 55.02842699999997, -58.75306600000002 55.02842699999997))'
        self.polarizations = ['HH', 'HV']
    
    def test_product_processing(self):
        # test read product
        product = read_product(self.product_path)
        bands = product.getBandNames()
        
        self.assertTrue(isinstance(product, snappy.Product))
        self.assertTrue('Amplitude_HH' in bands)
        self.assertTrue('Intensity_HH' in bands)
        self.assertTrue('Amplitude_HV' in bands)
        self.assertTrue('Intensity_HV' in bands)
        for band in product.getBands():
            self.assertTrue(band.getRasterWidth() == 25969)
            self.assertTrue(band.getRasterHeight() == 16659)
        
        # test apply orbit file
        product = apply_orbit_file(product)
        bands = product.getBandNames()
        
        self.assertTrue(isinstance(product, snappy.Product))
        self.assertTrue('Amplitude_HH' in bands)
        self.assertTrue('Intensity_HH' in bands)
        self.assertTrue('Amplitude_HV' in bands)
        self.assertTrue('Intensity_HV' in bands)
        for band in product.getBands():
            self.assertTrue(band.getRasterWidth() == 25969)
            self.assertTrue(band.getRasterHeight() == 16659)
        
        # test remove GRD border noise
        product = remove_grd_border_noise(product)
        bands = product.getBandNames()
        
        self.assertTrue(isinstance(product, snappy.Product))
        self.assertTrue('Amplitude_HH' in bands)
        self.assertTrue('Intensity_HH' in bands)
        self.assertTrue('Amplitude_HV' in bands)
        self.assertTrue('Intensity_HV' in bands)
        for band in product.getBands():
            self.assertTrue(band.getRasterWidth() == 25969)
            self.assertTrue(band.getRasterHeight() == 16659)
        
        # test remove thermal noise
        product = remove_thermal_noise(product)
        bands = product.getBandNames()
        
        self.assertTrue(isinstance(product, snappy.Product))
        self.assertFalse('Amplitude_HH' in bands)
        self.assertTrue('Intensity_HH' in bands)
        self.assertFalse('Amplitude_HV' in bands)
        self.assertTrue('Intensity_HV' in bands)
        for band in product.getBands():
            self.assertTrue(band.getRasterWidth() == 25969)
            self.assertTrue(band.getRasterHeight() == 16659)
        
        # test subset
        product = subset(product, self.wkt_aoi)
        bands = product.getBandNames()
        
        self.assertTrue(isinstance(product, snappy.Product))
        self.assertTrue('Intensity_HH' in bands)
        self.assertTrue('Intensity_HV' in bands)
        for band in product.getBands():
            self.assertTrue(band.getRasterWidth() == 403)
            self.assertTrue(band.getRasterHeight() == 594)
            
        
        for polarization in self.polarizations:
            # test calibrate
            subset_product = calibrate(product, polarization)
            bands = subset_product.getBandNames()
            
            self.assertTrue(isinstance(subset_product, snappy.Product))
            self.assertFalse('Intensity_HH' in bands)
            self.assertFalse('Intensity_HV' in bands)
            self.assertTrue(f'Sigma0_{polarization}' in bands)
            for band in subset_product.getBands():
                self.assertTrue(band.getRasterWidth() == 403)
                self.assertTrue(band.getRasterHeight() == 594)

            # test speckle filter
            subset_product = speckle_filter(subset_product, polarization)
            bands = subset_product.getBandNames()
            
            self.assertTrue(isinstance(subset_product, snappy.Product))
            self.assertTrue(f'Sigma0_{polarization}' in bands)
            for band in subset_product.getBands():
                self.assertTrue(band.getRasterWidth() == 403)
                self.assertTrue(band.getRasterHeight() == 594)
            
            # test terrain correction
            subset_product = terrain_correction(subset_product, polarization)
            bands = subset_product.getBandNames()
            
            self.assertTrue(isinstance(subset_product, snappy.Product))
            self.assertTrue(f'Sigma0_{polarization}' in bands)
            self.assertTrue('projectedLocalIncidenceAngle' in bands)
            for band in subset_product.getBands():
                self.assertTrue(band.getRasterWidth() == 852)
                self.assertTrue(band.getRasterHeight() == 652)
                
            # test scale in Db
            subset_product = scale_in_db(subset_product)
            bands = subset_product.getBandNames()
            
            self.assertTrue(isinstance(subset_product, snappy.Product))
            self.assertFalse(f'Sigma0_{polarization}' in bands)
            self.assertFalse('projectedLocalIncidenceAngle' in bands)
            self.assertTrue(f'Sigma0_{polarization}_db' in bands)
            self.assertTrue('projectedLocalIncidenceAngle_db' in bands)
            for band in subset_product.getBands():
                self.assertTrue(band.getRasterWidth() == 852)
                self.assertTrue(band.getRasterHeight() == 652)
