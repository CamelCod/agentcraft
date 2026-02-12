import { Client } from '@notionhq/client';
import type { 
  BlogPost, 
  AnalysisPost, 
  Resource, 
  NotionPage, 
  NotionBlock,
  NotionDatabaseQueryResult 
} from './types';

// Initialize Notion client
const notion = new Client({ auth: import.meta.env.NOTION_API_KEY });

// Cache for build-time data
const cache: Map<string, any> = new Map();

/**
 * Fetch all blog posts from Notion database
 */
export async function getBlogPosts(): Promise<BlogPost[]> {
  const cacheKey = 'blog_posts';
  
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }

  try {
    const databaseId = import.meta.env.NOTION_BLOG_DATABASE_ID;
    if (!databaseId) {
      console.warn('NOTION_BLOG_DATABASE_ID not set, returning mock data');
      return getMockBlogPosts();
    }

    const response = await notion.databases.query({
      database_id: databaseId,
      filter: {
        property: 'Status',
        select: {
          equals: 'Published'
        }
      },
      sorts: [
        {
          property: 'Published Date',
          direction: 'descending'
        }
      ]
    });

    const posts = response.results.map(page => convertPageToBlogPost(page as NotionPage));
    cache.set(cacheKey, posts);
    return posts;
  } catch (error) {
    console.error('Error fetching blog posts:', error);
    return getMockBlogPosts();
  }
}

/**
 * Fetch a single blog post by slug
 */
export async function getBlogPostBySlug(slug: string): Promise<BlogPost | null> {
  try {
    const posts = await getBlogPosts();
    return posts.find(post => post.slug === slug) || null;
  } catch (error) {
    console.error('Error fetching blog post by slug:', error);
    return null;
  }
}

/**
 * Fetch all analysis posts from Notion database
 */
export async function getAnalysisPosts(): Promise<AnalysisPost[]> {
  const cacheKey = 'analysis_posts';
  
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }

  try {
    const databaseId = import.meta.env.NOTION_ANALYSIS_DATABASE_ID;
    if (!databaseId) {
      console.warn('NOTION_ANALYSIS_DATABASE_ID not set, returning mock data');
      return getMockAnalysisPosts();
    }

    const response = await notion.databases.query({
      database_id: databaseId,
      filter: {
        property: 'Status',
        select: {
          equals: 'Published'
        }
      },
      sorts: [
        {
          property: 'Published Date',
          direction: 'descending'
        }
      ]
    });

    const posts = response.results.map(page => convertPageToAnalysisPost(page as NotionPage));
    cache.set(cacheKey, posts);
    return posts;
  } catch (error) {
    console.error('Error fetching analysis posts:', error);
    return getMockAnalysisPosts();
  }
}

/**
 * Fetch a single analysis post by slug
 */
export async function getAnalysisPostBySlug(slug: string): Promise<AnalysisPost | null> {
  try {
    const posts = await getAnalysisPosts();
    return posts.find(post => post.slug === slug) || null;
  } catch (error) {
    console.error('Error fetching analysis post by slug:', error);
    return null;
  }
}

/**
 * Fetch all resources from Notion database
 */
export async function getResources(): Promise<Resource[]> {
  const cacheKey = 'resources';
  
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }

  try {
    const databaseId = import.meta.env.NOTION_RESOURCES_DATABASE_ID;
    if (!databaseId) {
      console.warn('NOTION_RESOURCES_DATABASE_ID not set, returning mock data');
      return getMockResources();
    }

    const response = await notion.databases.query({
      database_id: databaseId
    });

    const resources = response.results.map(page => convertPageToResource(page as NotionPage));
    cache.set(cacheKey, resources);
    return resources;
  } catch (error) {
    console.error('Error fetching resources:', error);
    return getMockResources();
  }
}

/**
 * Fetch page content blocks from Notion
 */
export async function getPageContent(pageId: string): Promise<NotionBlock[]> {
  try {
    const response = await notion.blocks.children.list({
      block_id: pageId
    });

    return response.results as NotionBlock[];
  } catch (error) {
    console.error('Error fetching page content:', error);
    return [];
  }
}

/**
 * Add a lead to the Notion leads database
 */
export async function addLead(email: string, name: string, source: string, resource?: string): Promise<boolean> {
  try {
    const databaseId = import.meta.env.NOTION_LEADS_DATABASE_ID;
    if (!databaseId) {
      console.error('NOTION_LEADS_DATABASE_ID not set');
      return false;
    }

    await notion.pages.create({
      parent: { database_id: databaseId },
      properties: {
        'Email': {
          email: email
        },
        'Name': {
          rich_text: [{
            text: { content: name || '' }
          }]
        },
        'Source': {
          select: { name: source }
        },
        'Resource Downloaded': {
          rich_text: [{
            text: { content: resource || '' }
          }]
        }
      }
    });

    return true;
  } catch (error) {
    console.error('Error adding lead:', error);
    return false;
  }
}

/**
 * Convert Notion blocks to HTML
 */
export function blocksToHtml(blocks: NotionBlock[]): string {
  return blocks.map(block => blockToHtml(block)).join('');
}

function blockToHtml(block: NotionBlock): string {
  const type = block.type;
  
  switch (type) {
    case 'paragraph':
      return `<p>${richTextToHtml(block.paragraph?.rich_text || [])}</p>`;
    case 'heading_1':
      return `<h1>${richTextToHtml(block.heading_1?.rich_text || [])}</h1>`;
    case 'heading_2':
      return `<h2>${richTextToHtml(block.heading_2?.rich_text || [])}</h2>`;
    case 'heading_3':
      return `<h3>${richTextToHtml(block.heading_3?.rich_text || [])}</h3>`;
    case 'bulleted_list_item':
      return `<li>${richTextToHtml(block.bulleted_list_item?.rich_text || [])}</li>`;
    case 'numbered_list_item':
      return `<li>${richTextToHtml(block.numbered_list_item?.rich_text || [])}</li>`;
    case 'code':
      return `<pre><code class="language-${block.code?.language || 'plaintext'}">${richTextToHtml(block.code?.rich_text || [])}</code></pre>`;
    case 'quote':
      return `<blockquote>${richTextToHtml(block.quote?.rich_text || [])}</blockquote>`;
    case 'divider':
      return '<hr />';
    default:
      return '';
  }
}

function richTextToHtml(richText: any[]): string {
  return richText.map(text => {
    let html = text.plain_text;
    
    if (text.annotations?.bold) html = `<strong>${html}</strong>`;
    if (text.annotations?.italic) html = `<em>${html}</em>`;
    if (text.annotations?.strikethrough) html = `<del>${html}</del>`;
    if (text.annotations?.underline) html = `<u>${html}</u>`;
    if (text.annotations?.code) html = `<code>${html}</code>`;
    if (text.href) html = `<a href="${text.href}" target="_blank" rel="noopener noreferrer">${html}</a>`;
    
    return html;
  }).join('');
}

// Helper functions to convert Notion pages to typed objects
function convertPageToBlogPost(page: NotionPage): BlogPost {
  return {
    id: page.id,
    title: getPropertyValue(page.properties.Title, 'title'),
    slug: getPropertyValue(page.properties.Slug, 'rich_text'),
    status: getPropertyValue(page.properties.Status, 'select') || 'Draft',
    publishedDate: getPropertyValue(page.properties['Published Date'], 'date'),
    author: getPropertyValue(page.properties.Author, 'people'),
    tags: getPropertyValue(page.properties.Tags, 'multi_select') || [],
    featuredImage: getPropertyValue(page.properties['Featured Image'], 'files'),
    excerpt: getPropertyValue(page.properties.Excerpt, 'rich_text'),
    seoDescription: getPropertyValue(page.properties['SEO Description'], 'rich_text'),
    content: []
  };
}

function convertPageToAnalysisPost(page: NotionPage): AnalysisPost {
  return {
    id: page.id,
    title: getPropertyValue(page.properties.Title, 'title'),
    slug: getPropertyValue(page.properties.Slug, 'rich_text'),
    status: getPropertyValue(page.properties.Status, 'select') || 'Draft',
    analysisType: getPropertyValue(page.properties['Analysis Type'], 'select') || 'Market',
    publishedDate: getPropertyValue(page.properties['Published Date'], 'date'),
    industry: getPropertyValue(page.properties.Industry, 'select') || '',
    keyInsights: getPropertyValue(page.properties['Key Insights'], 'multi_select') || [],
    leadMagnet: getPropertyValue(page.properties['Lead Magnet'], 'checkbox') || false,
    downloadURL: getPropertyValue(page.properties['Download URL'], 'url'),
    content: []
  };
}

function convertPageToResource(page: NotionPage): Resource {
  return {
    id: page.id,
    title: getPropertyValue(page.properties.Title, 'title'),
    type: getPropertyValue(page.properties.Type, 'select') || 'Guide',
    description: getPropertyValue(page.properties.Description, 'rich_text'),
    gated: getPropertyValue(page.properties.Gated, 'checkbox') || false,
    downloadLink: getPropertyValue(page.properties['Download Link'], 'url'),
    coverImage: getPropertyValue(page.properties['Cover Image'], 'files'),
    tags: getPropertyValue(page.properties.Tags, 'multi_select') || []
  };
}

function getPropertyValue(property: any, type: string): any {
  if (!property) return null;
  
  switch (type) {
    case 'title':
      return property.title?.[0]?.plain_text || '';
    case 'rich_text':
      return property.rich_text?.[0]?.plain_text || '';
    case 'select':
      return property.select?.name || null;
    case 'multi_select':
      return property.multi_select?.map((item: any) => item.name) || [];
    case 'date':
      return property.date?.start || null;
    case 'checkbox':
      return property.checkbox || false;
    case 'url':
      return property.url || null;
    case 'email':
      return property.email || null;
    case 'people':
      return property.people?.[0]?.name || 'Anonymous';
    case 'files':
      return property.files?.[0]?.file?.url || property.files?.[0]?.external?.url || null;
    default:
      return null;
  }
}

// Constants for date calculations
const MILLISECONDS_PER_DAY = 24 * 60 * 60 * 1000;

// Mock data functions for development without Notion API
function getMockBlogPosts(): BlogPost[] {
  const now = Date.now();
  return [
    {
      id: '1',
      title: 'Getting Started with AgentCraft',
      slug: 'getting-started-agentcraft',
      status: 'Published',
      publishedDate: new Date(now).toISOString(),
      author: 'AgentCraft Team',
      tags: ['Tutorial', 'Getting Started'],
      excerpt: 'Learn how to get started with AgentCraft and build your first intelligent agent.',
      seoDescription: 'A comprehensive guide to getting started with AgentCraft for building intelligent agents.',
      content: []
    },
    {
      id: '2',
      title: 'Building Your First AI Agent',
      slug: 'building-first-ai-agent',
      status: 'Published',
      publishedDate: new Date(now - MILLISECONDS_PER_DAY).toISOString(),
      author: 'AgentCraft Team',
      tags: ['Tutorial', 'AI', 'Automation'],
      excerpt: 'Step-by-step guide to creating your first AI agent with AgentCraft.',
      seoDescription: 'Learn to build your first AI agent with this comprehensive tutorial.',
      content: []
    },
    {
      id: '3',
      title: 'Advanced Agent Patterns',
      slug: 'advanced-agent-patterns',
      status: 'Published',
      publishedDate: new Date(now - (2 * MILLISECONDS_PER_DAY)).toISOString(),
      author: 'AgentCraft Team',
      tags: ['Advanced', 'Patterns', 'Best Practices'],
      excerpt: 'Explore advanced patterns and best practices for building sophisticated agents.',
      seoDescription: 'Master advanced agent patterns and best practices with AgentCraft.',
      content: []
    }
  ];
}

function getMockAnalysisPosts(): AnalysisPost[] {
  return [
    {
      id: '1',
      title: 'State of AI Automation in 2024',
      slug: 'state-ai-automation-2024',
      status: 'Published',
      analysisType: 'Market',
      publishedDate: new Date().toISOString(),
      industry: 'AI',
      keyInsights: ['Market Growth', 'Key Players', 'Future Trends'],
      leadMagnet: true,
      downloadURL: '#',
      content: []
    }
  ];
}

function getMockResources(): Resource[] {
  return [
    {
      id: '1',
      title: 'Agent Development Checklist',
      type: 'Checklist',
      description: 'A comprehensive checklist for developing production-ready AI agents.',
      gated: false,
      downloadLink: '#',
      tags: ['Development', 'Best Practices']
    },
    {
      id: '2',
      title: 'AI Agent Architecture Guide',
      type: 'Guide',
      description: 'Complete guide to designing scalable AI agent architectures.',
      gated: true,
      downloadLink: '#',
      tags: ['Architecture', 'Advanced']
    }
  ];
}

/**
 * Calculate reading time for content
 */
export function calculateReadingTime(content: string): number {
  const wordsPerMinute = 200;
  const wordCount = content.split(/\s+/).length;
  return Math.ceil(wordCount / wordsPerMinute);
}
