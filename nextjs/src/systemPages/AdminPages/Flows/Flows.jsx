'use client';
import AdminPageLayout from "../AdminPageLayout"
import FlowsDashboard from "./Dashboard/FlowsDashboard"



export default function FlowsPage({ authData }) {
  return (
    <AdminPageLayout authData={authData}>
      <FlowsDashboard/>
    </AdminPageLayout>
  )
}