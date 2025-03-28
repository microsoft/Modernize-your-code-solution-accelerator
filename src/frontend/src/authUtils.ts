import { getUserInfo } from "./api/auth";

export async function GetAuthDetails() {
    const userInfo = await getUserInfo();
    if (!userInfo) {
      return null;
    }
  
    return {
      'Content-Type': 'application/json',
      'X-Ms-Client-Principal': userInfo.id_token || '',
      'X-Ms-Client-Principal-Id': userInfo.user_claims?.find(claim => claim.typ === 'http://schemas.microsoft.com/identity/claims/objectidentifier')?.val || '',
      'X-Ms-Client-Principal-Name': userInfo.user_claims?.find(claim => claim.typ === 'name')?.val || '',
      'X-Ms-Client-Principal-Idp': userInfo.provider_name || '',
    };
  }
  