export type UserInfo = {
  access_token: string;
  expires_on: string;
  id_token: string;
  provider_name: string;
  user_claims: any[];
  user_id: string;
};

export async function getUserInfo(): Promise<UserInfo | null> {
  try {
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      // Fetch auth details from Azure
      const response = await fetch("/.auth/me");
      if (!response.ok) {
        console.log("No identity provider found. Access to app will be blocked.");
        return null;
      }

      let authData;
      const contentType = response.headers.get("content-type");

      if (contentType && contentType.includes("application/json")) {
        authData = await response.json();
      } else {
        authData = await response.text(); // Fallback for non-JSON responses
      }
      if (!Array.isArray(authData) || authData.length === 0) {
        console.log("No user details found.");
        return null;
      }
      const userDetails = authData[0];

      return {
        access_token: userDetails?.access_token || '',
        expires_on: userDetails?.expires_on || '',
        id_token: userDetails?.id_token || '',
        provider_name: userDetails?.provider_name || '',
        user_claims: userDetails?.user_claims || [],
        user_id: userDetails?.user_id || '',
      };
    } else {
      // Running locally, use mock data
      console.log("Running locally. Skipping authentication details fetch.");

      return {
        access_token: 'mock-access-token',
        expires_on: new Date().toISOString(),
        id_token: 'mock-id-token',
        provider_name: 'mock-provider',
        user_claims: [
          { typ: 'http://schemas.microsoft.com/identity/claims/objectidentifier', val: '00000000-0000-0000-0000-000000000000' },
          { typ: 'name', val: 'Local User' },
          { typ: 'email', val: 'localuser@example.com' },
        ],
        user_id: 'mock-user-id',
      };
    }
  } catch (e) {
    console.error("Error fetching authentication details:", e);
    return null;
  }
}