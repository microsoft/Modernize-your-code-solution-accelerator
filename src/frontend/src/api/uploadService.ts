import axios from 'axios';
import { getApiUrl, getUserId } from './config';

export const uploadFiles = async (files: File[]): Promise<any[]> => {
  const responses: any[] = [];

  for (let file of files) {
    const formData = new FormData();
    console.log(file)
    formData.append('file', file); // Use 'file' instead of 'files' for single file upload
    console.log(`Uploading file ${file.name}...`);
    console.log(formData)
    try {
      const apiUrl = getApiUrl();
      const userId = getUserId();
      const response = await axios.post(`${apiUrl}/upload`, file, {
        headers: {
          'Content-Type': 'multipart/form-data',
          "x-ms-client-principal-id": String(userId) ?? "",  // Custom header
        },
      });
      responses.push(response.data);
    } catch (error) {
      console.error(`Error uploading file ${file.name}:`, error);
      responses.push({ file: file.name, error: error.message });
    }
  }

  return responses;
};
