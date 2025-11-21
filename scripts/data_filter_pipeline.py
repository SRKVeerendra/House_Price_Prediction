#!/usr/bin/env python3
"""
House Price Data Filtering and Cleaning Pipeline
================================================

This script loads house pricing datasets, analyzes data quality,
removes null values, applies filters, and saves cleaned data.

Author: Data Analysis Team
Date: November 2025
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
import json
import warnings
warnings.filterwarnings('ignore')

class HousePriceDataFilter:
    def __init__(self, input_dir="dataset_house_pricing", output_dir="output/filter_data"):
        # Get the parent directory (go up one level from scripts folder)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        
        # Set paths relative to parent directory
        self.input_dir = os.path.join(parent_dir, input_dir)
        self.output_dir = os.path.join(parent_dir, output_dir)
        self.datasets = {}
        self.filtered_datasets = {}
        self.data_quality_report = {}
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_all_datasets(self):
        """Load all CSV files from the input directory"""
        print("🔄 Loading datasets...")
        
        csv_files = [f for f in os.listdir(self.input_dir) if f.endswith('.csv')]
        
        for filename in csv_files:
            filepath = os.path.join(self.input_dir, filename)
            dataset_name = filename.replace('.csv', '').replace(' ', '_').lower()
            
            try:
                # Try different encodings
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    try:
                        df = pd.read_csv(filepath, encoding=encoding)
                        # Store both the dataframe and original filename
                        self.datasets[dataset_name] = {
                            'data': df,
                            'filename': filename
                        }
                        print(f"✅ Loaded {filename} - Shape: {df.shape}")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    print(f"❌ Could not load {filename} - encoding issues")
                    
            except Exception as e:
                print(f"❌ Error loading {filename}: {str(e)}")
        
        print(f"\n📊 Successfully loaded {len(self.datasets)} datasets")
        return self.datasets
    
    def analyze_data_quality(self):
        """Analyze data quality for each dataset"""
        print("\n🔍 Analyzing data quality...")
        
        for name, dataset_info in self.datasets.items():
            df = dataset_info['data']
            filename = dataset_info['filename']
            print(f"\n📋 Dataset: {filename} ({name})")
            
            quality_info = {
                'filename': filename,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'columns': list(df.columns),
                'data_types': df.dtypes.to_dict(),
                'null_counts': df.isnull().sum().to_dict(),
                'null_percentages': (df.isnull().sum() / len(df) * 100).to_dict(),
                'duplicate_rows': df.duplicated().sum(),
                'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2
            }
            
            self.data_quality_report[name] = quality_info
            
            # Display key statistics
            print(f"   📏 Shape: {quality_info['total_rows']:,} rows × {quality_info['total_columns']} columns")
            print(f"   🔄 Duplicates: {quality_info['duplicate_rows']:,}")
            print(f"   💾 Memory: {quality_info['memory_usage_mb']:.2f} MB")
            
            # Show null value statistics
            null_cols = [(col, count, pct) for col, count, pct in 
                        zip(quality_info['null_counts'].keys(), 
                           quality_info['null_counts'].values(),
                           quality_info['null_percentages'].values()) 
                        if count > 0]
            
            if null_cols:
                print(f"   ❗ Columns with null values:")
                for col, count, pct in sorted(null_cols, key=lambda x: x[1], reverse=True)[:10]:
                    print(f"      {col}: {count:,} ({pct:.1f}%)")
            else:
                print(f"   ✅ No null values found")
    
    def filter_india_detailed_data(self, df):
        """Filter and clean India house price data"""
        print("   🔧 Applying India-specific filters...")
        
        original_rows = len(df)
        
        # Remove rows with null prices (essential column)
        if 'Price' in df.columns:
            df = df.dropna(subset=['Price'])
            # Remove unrealistic prices (less than ₹50,000 or more than ₹50,00,00,000)
            df = df[(df['Price'] >= 50000) & (df['Price'] <= 500000000)]
        
        # Remove rows with impossible bedroom/bathroom counts
        if 'number of bedrooms' in df.columns:
            df = df[(df['number of bedrooms'] >= 1) & (df['number of bedrooms'] <= 20)]
        
        if 'number of bathrooms' in df.columns:
            df = df[(df['number of bathrooms'] >= 0.5) & (df['number of bathrooms'] <= 15)]
        
        # Remove rows with impossible areas
        if 'living area' in df.columns:
            df = df[(df['living area'] > 0) & (df['living area'] <= 50000)]
        
        if 'lot area' in df.columns:
            df = df[(df['lot area'] > 0) & (df['lot area'] <= 1000000)]
        
        # Remove rows with invalid coordinates (if they exist)
        if 'Lattitude' in df.columns and 'Longitude' in df.columns:
            df = df.dropna(subset=['Lattitude', 'Longitude'])
            # Remove coordinates that are clearly invalid (0,0 or extreme values)
            df = df[~((df['Lattitude'] == 0) & (df['Longitude'] == 0))]
        
        # Remove rows with invalid years
        if 'Built Year' in df.columns:
            current_year = datetime.now().year
            df = df[(df['Built Year'] >= 1800) & (df['Built Year'] <= current_year)]
        
        print(f"      Removed {original_rows - len(df):,} rows ({((original_rows - len(df))/original_rows)*100:.1f}%)")
        return df
    
    def filter_king_county_data(self, df):
        """Filter and clean King County house price data"""
        print("   🔧 Applying King County-specific filters...")
        
        original_rows = len(df)
        
        # Remove rows with null prices
        if 'price' in df.columns:
            df = df.dropna(subset=['price'])
            # Remove unrealistic prices (less than $10,000 or more than $50,000,000)
            df = df[(df['price'] >= 10000) & (df['price'] <= 50000000)]
        
        # Remove impossible bedroom/bathroom counts
        if 'bedrooms' in df.columns:
            df = df[(df['bedrooms'] >= 0) & (df['bedrooms'] <= 20)]
        
        if 'bathrooms' in df.columns:
            df = df[(df['bathrooms'] >= 0) & (df['bathrooms'] <= 15)]
        
        # Remove impossible square footage
        if 'sqft_living' in df.columns:
            df = df[(df['sqft_living'] > 0) & (df['sqft_living'] <= 20000)]
        
        if 'sqft_lot' in df.columns:
            df = df[(df['sqft_lot'] > 0) & (df['sqft_lot'] <= 2000000)]
        
        # Remove invalid coordinates
        if 'lat' in df.columns and 'long' in df.columns:
            df = df.dropna(subset=['lat', 'long'])
            # King County coordinates roughly: lat 47.0-48.0, long -122.6 to -121.0
            df = df[(df['lat'] >= 47.0) & (df['lat'] <= 48.0)]
            df = df[(df['long'] >= -122.6) & (df['long'] <= -121.0)]
        
        # Remove invalid years
        if 'yr_built' in df.columns:
            current_year = datetime.now().year
            df = df[(df['yr_built'] >= 1800) & (df['yr_built'] <= current_year)]
        
        # Remove invalid grades
        if 'grade' in df.columns:
            df = df[(df['grade'] >= 1) & (df['grade'] <= 13)]
        
        print(f"      Removed {original_rows - len(df):,} rows ({((original_rows - len(df))/original_rows)*100:.1f}%)")
        return df
    
    def filter_international_data(self, df):
        """Filter and clean international house price data"""
        print("   🔧 Applying international data filters...")
        
        original_rows = len(df)
        
        # Convert date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date'])
        
        # Remove rows where price is null AND we want to keep the data structure
        # For international data, we might want to keep rows with null prices for some analysis
        # but we'll create a version with price data only
        df_with_prices = df.dropna(subset=['price']) if 'price' in df.columns else df
        
        # Remove extreme outliers in price changes (more than ±200% change seems unrealistic)
        if 'price' in df.columns:
            df_with_prices = df_with_prices[(df_with_prices['price'] >= -200) & (df_with_prices['price'] <= 200)]
        
        print(f"      Removed {original_rows - len(df_with_prices):,} rows ({((original_rows - len(df_with_prices))/original_rows)*100:.1f}%)")
        return df_with_prices
    
    def filter_india_index_data(self, df):
        """Filter and clean India price index data"""
        print("   🔧 Applying India index data filters...")
        
        original_rows = len(df)
        
        # This data might have a different structure, so we'll be more careful
        # Remove completely empty rows
        df = df.dropna(how='all')
        
        # For numeric columns, remove unrealistic index values
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Price indices typically range from 50 to 500 (assuming base 100)
            df = df[(df[col].isna()) | ((df[col] >= 10) & (df[col] <= 1000))]
        
        print(f"      Removed {original_rows - len(df):,} rows ({((original_rows - len(df))/original_rows)*100:.1f}%)")
        return df
    
    def apply_filters(self):
        """Apply appropriate filters to each dataset"""
        print("\n🔄 Applying data filters...")
        
        for name, dataset_info in self.datasets.items():
            df = dataset_info['data']
            filename = dataset_info['filename']
            print(f"\n📊 Processing: {filename}")
            
            # Apply dataset-specific filters based on filename or content
            if 'india' in filename.lower() and 'index' not in filename.lower():
                filtered_df = self.filter_india_detailed_data(df.copy())
            elif any(keyword in filename.lower() for keyword in ['house_prices', 'housing']):
                filtered_df = self.filter_king_county_data(df.copy())
            elif any(keyword in filename.lower() for keyword in ['real_year', 'nominal_year', 'real_index', 'nominal_index']):
                filtered_df = self.filter_international_data(df.copy())
            elif 'index' in filename.lower():
                filtered_df = self.filter_india_index_data(df.copy())
            else:
                # Generic filtering for unknown datasets
                print("   🔧 Applying generic filters...")
                original_rows = len(df)
                filtered_df = df.dropna(how='all')  # Remove completely empty rows
                filtered_df = filtered_df.drop_duplicates()  # Remove duplicates
                print(f"      Removed {original_rows - len(filtered_df):,} rows ({((original_rows - len(filtered_df))/original_rows)*100:.1f}%)")
            
            self.filtered_datasets[name] = {
                'data': filtered_df,
                'filename': filename
            }
            
            # Show filtering results
            original_shape = df.shape
            filtered_shape = filtered_df.shape
            print(f"   📏 Original: {original_shape[0]:,} rows × {original_shape[1]} cols")
            print(f"   📏 Filtered: {filtered_shape[0]:,} rows × {filtered_shape[1]} cols")
            print(f"   📈 Data retention: {(filtered_shape[0]/original_shape[0])*100:.1f}%")
    
    def save_filtered_data(self):
        """Save all filtered datasets to the output directory"""
        print(f"\n💾 Saving filtered datasets to '{self.output_dir}'...")
        
        for name, dataset_info in self.filtered_datasets.items():
            df = dataset_info['data']
            original_filename = dataset_info['filename']
            output_path = os.path.join(self.output_dir, original_filename)
            
            try:
                df.to_csv(output_path, index=False, encoding='utf-8')
                print(f"   ✅ Saved {original_filename} ({len(df):,} rows)")
            except Exception as e:
                print(f"   ❌ Error saving {original_filename}: {str(e)}")
    
    def generate_data_quality_report(self):
        """Generate and save a comprehensive data quality report"""
        print("\n📊 Generating data quality report...")
        
        report = {
            'analysis_date': datetime.now().isoformat(),
            'summary': {
                'total_datasets': len(self.datasets),
                'datasets_processed': len(self.filtered_datasets),
                'total_original_rows': sum(len(info['data']) for info in self.datasets.values()),
                'total_filtered_rows': sum(len(info['data']) for info in self.filtered_datasets.values())
            },
            'datasets': {}
        }
        
        for name in self.datasets.keys():
            original_df = self.datasets[name]['data']
            filtered_info = self.filtered_datasets.get(name)
            
            dataset_report = {
                'filename': self.datasets[name]['filename'],
                'original_shape': original_df.shape,
                'original_columns': list(original_df.columns),
                'original_null_counts': original_df.isnull().sum().to_dict(),
                'original_duplicates': original_df.duplicated().sum(),
            }
            
            if filtered_info is not None:
                filtered_df = filtered_info['data']
                dataset_report.update({
                    'filtered_shape': filtered_df.shape,
                    'filtered_null_counts': filtered_df.isnull().sum().to_dict(),
                    'filtered_duplicates': filtered_df.duplicated().sum(),
                    'rows_removed': original_df.shape[0] - filtered_df.shape[0],
                    'retention_rate': (filtered_df.shape[0] / original_df.shape[0]) * 100 if original_df.shape[0] > 0 else 0
                })
            
            report['datasets'][name] = dataset_report
        
        # Save JSON report
        report_path = os.path.join(self.output_dir, 'data_quality_report.json')
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Save human-readable report
        readable_report_path = os.path.join(self.output_dir, 'data_quality_report.txt')
        with open(readable_report_path, 'w', encoding='utf-8') as f:
            f.write("HOUSE PRICE DATA QUALITY REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("SUMMARY:\n")
            f.write(f"  Total Datasets: {report['summary']['total_datasets']}\n")
            f.write(f"  Datasets Processed: {report['summary']['datasets_processed']}\n")
            f.write(f"  Original Total Rows: {report['summary']['total_original_rows']:,}\n")
            f.write(f"  Filtered Total Rows: {report['summary']['total_filtered_rows']:,}\n")
            f.write(f"  Overall Retention Rate: {(report['summary']['total_filtered_rows']/report['summary']['total_original_rows'])*100:.1f}%\n\n")
            
            for name, data in report['datasets'].items():
                f.write(f"{name.upper()}:\n")
                f.write(f"  Original Shape: {data['original_shape'][0]:,} rows × {data['original_shape'][1]} columns\n")
                if 'filtered_shape' in data:
                    f.write(f"  Filtered Shape: {data['filtered_shape'][0]:,} rows × {data['filtered_shape'][1]} columns\n")
                    f.write(f"  Rows Removed: {data['rows_removed']:,}\n")
                    f.write(f"  Retention Rate: {data['retention_rate']:.1f}%\n")
                f.write(f"  Original Duplicates: {data['original_duplicates']:,}\n")
                
                # Show top null columns
                null_counts = data['original_null_counts']
                top_nulls = sorted([(k, v) for k, v in null_counts.items() if v > 0], 
                                 key=lambda x: x[1], reverse=True)[:5]
                if top_nulls:
                    f.write("  Top Null Columns (original):\n")
                    for col, count in top_nulls:
                        pct = (count / data['original_shape'][0]) * 100
                        f.write(f"    {col}: {count:,} ({pct:.1f}%)\n")
                f.write("\n")
        
        print(f"   ✅ Data quality report saved to data_quality_report.json and .txt")
        
        # Print summary to console
        print(f"\n📊 FILTERING SUMMARY:")
        print(f"   Original rows: {report['summary']['total_original_rows']:,}")
        print(f"   Filtered rows: {report['summary']['total_filtered_rows']:,}")
        print(f"   Overall retention: {(report['summary']['total_filtered_rows']/report['summary']['total_original_rows'])*100:.1f}%")
    
    def run_pipeline(self):
        """Run the complete data filtering pipeline"""
        print("🚀 Starting House Price Data Filtering Pipeline")
        print("=" * 60)
        
        # Step 1: Load all datasets
        self.load_all_datasets()
        
        # Step 2: Analyze data quality
        self.analyze_data_quality()
        
        # Step 3: Apply filters
        self.apply_filters()
        
        # Step 4: Save filtered data
        self.save_filtered_data()
        
        # Step 5: Generate report
        self.generate_data_quality_report()
        
        print("\n🎉 Data filtering pipeline completed successfully!")
        print(f"📁 Filtered datasets saved in: {self.output_dir}")
        print("📊 Check data_quality_report.txt for detailed analysis")

def main():
    """Main function to run the data filtering pipeline"""
    # Initialize the filter pipeline
    # Paths will be automatically resolved relative to the script location
    filter_pipeline = HousePriceDataFilter()
    
    # Print the paths being used
    print(f"📁 Input directory: {filter_pipeline.input_dir}")
    print(f"📁 Output directory: {filter_pipeline.output_dir}")
    
    # Run the complete pipeline
    filter_pipeline.run_pipeline()

if __name__ == "__main__":
    main()