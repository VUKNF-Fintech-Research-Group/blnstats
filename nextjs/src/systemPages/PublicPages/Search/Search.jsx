'use client';
import PublicPageLayout from "@/systemPages/PublicPages/PublicPageLayout"
import Image from 'next/image';


export default function Search({ authData }) {

  

  return (
    <PublicPageLayout authData={authData} fullWidth={true}>
      {(authData) => (
        <div className="flex flex-col">

          {/* Search */}
          <h2 className="text-2xl font-bold text-left">Search</h2>
          <p className="text-left mb-4">
            Search for a node/entity by its public key.
          </p>
          <input type="text" placeholder="Search" className="w-full p-2 rounded-md border border-gray-300" />
          <button className="bg-blue-500 text-white p-2 rounded-md">Search</button>

          

        </div>
      )}
    </PublicPageLayout>
  );
}