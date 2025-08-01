import EndpointWrapper from "@/components/ServerSide/EndpointWrapper";


// Page Components
import FlowsPage from "@/systemPages/AdminPages/Flows/Flows";

// Settings
const THIS_FILE_PATH = "/app/admin/page.jsx";
const REDIRECT_TO_LOGIN_URL = "/login";
const BACKEND_CHECK_AUTH_URL = process.env.API_INTERNAL + '/api/checkauth';
const IS_SECURED = true;


export default async function Page() {
  return (
    <EndpointWrapper 
      THIS_FILE_PATH={THIS_FILE_PATH} 
      REDIRECT_TO_LOGIN_URL={REDIRECT_TO_LOGIN_URL} 
      BACKEND_CHECK_AUTH_URL={BACKEND_CHECK_AUTH_URL}
      isSecured={IS_SECURED}
    >
      {(authData) => <FlowsPage authData={authData}/>}
    </EndpointWrapper>
  )
}