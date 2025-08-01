import EndpointWrapper from "@/components/ServerSide/EndpointWrapper";


// Page Components
import AboutPage from "@/systemPages/PublicPages/About/About";

// Settings
const THIS_FILE_PATH = "/app/about/page.jsx";
const REDIRECT_TO_LOGIN_URL = "/login";
const BACKEND_CHECK_AUTH_URL = process.env.API_INTERNAL + '/api/checkauth';
const IS_SECURED = false;


export default async function Page() {
  return (
    <EndpointWrapper 
      THIS_FILE_PATH={THIS_FILE_PATH} 
      REDIRECT_TO_LOGIN_URL={REDIRECT_TO_LOGIN_URL} 
      BACKEND_CHECK_AUTH_URL={BACKEND_CHECK_AUTH_URL}
      isSecured={IS_SECURED}
    >
      {(authData) => <AboutPage authData={authData}/>}
    </EndpointWrapper>
  )
}