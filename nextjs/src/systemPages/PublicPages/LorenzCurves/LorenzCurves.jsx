'use client';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
import Image from 'next/image';


export default function LorenzCurves({ authData }) {

  

  return (
    <PublicPageLayout authData={authData} fullWidth={true}>
      {(authData) => (
        <div className="flex flex-col">

          {/* Degree */}
          <h2 className="text-2xl font-bold text-left">Degree</h2>
          <p className="text-left mb-4">
            The degree of a node/entity is the number of channels it has.
          </p>
          <Image 
            src={"/rawdata/GENERATED/Nodes/degree/Lorenz_Curves/20XX-03-01/10x6_Full.svg?inline=true"} 
            alt="Lorenz Curves" 
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
          <Image 
            src={"/rawdata/GENERATED/Entities/degree/Lorenz_Curves/20XX-03-01/10x6_Full.svg?inline=true"} 
            alt="Lorenz Curves" 
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


          {/* Divider */}
          <div className="w-full border-t border-gray-300 mt-18 mb-8"></div>

          {/* Weighted Degree */}
          <h2 className="text-2xl font-bold text-left">Weighted Degree</h2>
          <p className="text-left mb-4">
            The weighted degree of a node/entity is the sum of the capacities of all its channels.
          </p>

          <Image 
            src={"/rawdata/GENERATED/Nodes/weighted_degree/Lorenz_Curves/20XX-03-01/10x6_Full.svg?inline=true"} 
            alt="Lorenz Curves" 
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
          <Image 
            src={"/rawdata/GENERATED/Entities/weighted_degree/Lorenz_Curves/20XX-03-01/10x6_Full.svg?inline=true"} 
            alt="Lorenz Curves" 
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


          {/* Divider */}
          <div className="w-full border-t border-gray-300 mt-18 mb-8"></div>

          

        </div>
      )}
    </PublicPageLayout>
  );
}