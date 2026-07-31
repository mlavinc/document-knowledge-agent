import axios, { AxiosInstance } from "axios";

export function createHttpClient(
  baseURL: string,
  defaultHeaders?: Record<string, string>
): AxiosInstance {
  return axios.create({
    baseURL,
    headers: defaultHeaders,
  });
}
