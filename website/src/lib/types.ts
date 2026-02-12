// TypeScript types and interfaces for the website

export interface NotionPage {
  id: string;
  created_time: string;
  last_edited_time: string;
  properties: Record<string, any>;
}

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  status: 'Draft' | 'Published' | 'Scheduled';
  publishedDate: string | null;
  author: string;
  tags: string[];
  featuredImage?: string;
  excerpt: string;
  seoDescription: string;
  content: NotionBlock[];
}

export interface AnalysisPost {
  id: string;
  title: string;
  slug: string;
  status: 'Draft' | 'Published';
  analysisType: 'Market' | 'Technical' | 'Case Study';
  publishedDate: string | null;
  industry: string;
  keyInsights: string[];
  leadMagnet: boolean;
  downloadURL?: string;
  content: NotionBlock[];
}

export interface Resource {
  id: string;
  title: string;
  type: 'eBook' | 'Template' | 'Guide' | 'Checklist';
  description: string;
  gated: boolean;
  downloadLink?: string;
  coverImage?: string;
  tags: string[];
}

export interface Lead {
  email: string;
  name?: string;
  source: 'Blog' | 'Analysis' | 'Resource';
  resourceDownloaded?: string;
}

export interface NotionBlock {
  type: string;
  [key: string]: any;
}

export interface NotionDatabaseQueryResult {
  results: NotionPage[];
  has_more: boolean;
  next_cursor: string | null;
}
