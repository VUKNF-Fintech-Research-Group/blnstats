'use client';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
import Image from 'next/image';
import { useState, useEffect } from 'react';
import VennDiagramChart from './components/VennDiagramChart';

export default function DataSourcesPage({ authData }) {
  const [comparisonData, setComparisonData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch the comparison data from the backend
    const fetchComparisonData = async () => {
      try {
        const response = await fetch('/rawdata/GENERATED/Compare_Sources/Channel_Announcements/compare_sources.json');
        if (response.ok) {
          const data = await response.json();
          setComparisonData(data);
        } else {
          setError('Failed to load comparison data');
        }
      } catch (err) {
        setError('Error fetching comparison data');
        console.error('Error fetching comparison data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchComparisonData();
  }, []);

  return (
    <PublicPageLayout authData={authData} fullWidth={true}>
      {(authData) => (
        <div className="flex flex-col">

          {/* Header */}
          <h2 className="text-2xl font-bold text-left">Data Sources</h2>
          <p className="text-left mb-6">
            The data sources that were used in the research.
          </p>

          {/* Venn Diagram showing overlap */}
          <div className="mb-8 flex justify-center p-4">
            <div className="w-full">
              {loading ? (
                <div className="flex justify-center p-8">
                  <div className="text-gray-500">Loading comparison data...</div>
                </div>
              ) : error ? (
                <div className="flex justify-center p-8">
                  <div className="text-red-500">{error}</div>
                </div>
              ) : (
                <div className="w-full">
                  {/* Large screens */}
                  <div className="hidden md:block">
                    <VennDiagramChart data={comparisonData} width={1000} height={600} />
                  </div>
                  {/* Small screens */}
                  <div className="block md:hidden">
                    <VennDiagramChart data={comparisonData} width={350} height={300} />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Time series chart */}
          <div className="mb-6">
            <h3 className="text-xl font-semibold mb-4">Data Sources Over Time</h3>
            <Image 
              src={"/rawdata/GENERATED/Compare_Sources/Channel_Announcements/20XX-03-01/10x6_Full.svg"} 
              alt="Data Sources Over Time" 
              width={1000} 
              height={1000} 
              className="m-4 rounded-lg shadow-lg" 
              style={{
                maxWidth: '100%',
                height: 'auto'
              }}
              onError={(e) => {
                e.target.src = "/no-data-found.jpeg";
              }}
            />
          </div>

          {/* Divider */}
          <div className="w-full border-t border-gray-300 mt-8 mb-8"></div>

        </div>
      )}
    </PublicPageLayout>
  );
}