'use client';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
import Image from 'next/image';


export default function Snapshots({ authData }) {

  

  return (
    <PublicPageLayout authData={authData} fullWidth={true}>
      {(authData) => (
        <div className="flex flex-col">

          {/* Entities Across Time */}
          <h2 className="text-2xl font-bold text-left">Entities Shares Across Time (Up to 2025-07-01)</h2>
          <p className="text-left mb-4">
            The share of network capacity held by each entity, visualized over time.
          </p>
          <img 
            src={"/rawdata/GENERATED/Snapshots/2025-07-01-Lines.svg"} 
            alt="Lorenz Curves"
            className="m-4 rounded-lg shadow-lg" 
            style={{
              maxWidth: '100%',
              height: 'auto',
              padding: '10px',
              backgroundColor: 'white',
            }}
            onError={(e) => {
              e.target.src = "/no-data-found.jpeg";
            }}
          />


          {/* Divider */}
          <div className="w-full border-t border-gray-300 mt-18 mb-8"></div>

          {/* Weighted Degree */}
          <h2 className="text-2xl font-bold text-left">Entities Sizes (At 2025-03-01)</h2>
          <p className="text-left mb-4">
            The share of network capacity held by each entity, visualized at a specific moment in time.
          </p>

          <img 
            src={"/rawdata/GENERATED/Snapshots/2025-03-01-Bubles.svg"} 
            alt="Lorenz Curves"
            className="m-4 rounded-lg shadow-lg" 
            style={{
              maxWidth: '100%',
              height: 'auto',
              padding: '10px',
              backgroundColor: 'white',
            }}
            onError={(e) => {
              e.target.src = "/no-data-found.jpeg";
            }}
          />

          {/* Divider */}
          <div className="w-full border-t border-gray-300 mt-18 mb-8"></div>

          

        </div>
      )}
    </PublicPageLayout>
  );
}