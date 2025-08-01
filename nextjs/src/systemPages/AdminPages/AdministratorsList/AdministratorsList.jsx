'use client';
import AdminPageLayout from "../AdminPageLayout"
import AdministratorsListTable from "./AdministratorsListTable/AdministratorsListTable"



export default function AdministratorsListPage() {
  return (
    <AdminPageLayout>
      <AdministratorsListTable/>
    </AdminPageLayout>
  )
}