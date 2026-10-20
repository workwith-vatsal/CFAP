import { apiClient } from './apiClient';
import {
  Dataset,
  DatasetListResponse,
  DataQualityReport,
  DataPreviewResponse,
  MessageResponse,
} from '@/types';

export async function uploadDataset(
  file: File,
  name?: string
): Promise<Dataset> {
  const formData = new FormData();
  formData.append('file', file);
  if (name && name.trim()) {
    formData.append('name', name.trim());
  }

  return apiClient.post<Dataset>('/api/v1/datasets/upload', formData);
}

export async function getDatasets(
  includeArchived: boolean = false
): Promise<DatasetListResponse> {
  const query = includeArchived ? '?include_archived=true' : '';
  return apiClient.get<DatasetListResponse>(`/api/v1/datasets${query}`);
}

export async function getDataset(id: number): Promise<Dataset> {
  return apiClient.get<Dataset>(`/api/v1/datasets/${id}`);
}

export async function getDatasetQuality(id: number): Promise<DataQualityReport> {
  return apiClient.get<DataQualityReport>(`/api/v1/datasets/${id}/quality`);
}

export async function getDatasetPreview(id: number): Promise<DataPreviewResponse> {
  return apiClient.get<DataPreviewResponse>(`/api/v1/datasets/${id}/preview`);
}

export async function renameDataset(
  id: number,
  name: string
): Promise<Dataset> {
  return apiClient.patch<Dataset>(`/api/v1/datasets/${id}`, { name });
}

export async function archiveDataset(id: number): Promise<Dataset> {
  return apiClient.post<Dataset>(`/api/v1/datasets/${id}/archive`);
}

export async function restoreDataset(id: number): Promise<Dataset> {
  return apiClient.post<Dataset>(`/api/v1/datasets/${id}/restore`);
}

export async function deleteDataset(id: number): Promise<MessageResponse> {
  return apiClient.delete<MessageResponse>(`/api/v1/datasets/${id}`);
}
