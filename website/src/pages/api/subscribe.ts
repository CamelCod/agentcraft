import type { APIRoute } from 'astro';
import { addLead } from '../../lib/notion';
import { sendWelcomeEmail, sendResourceEmail } from '../../lib/email';

export const POST: APIRoute = async ({ request }) => {
  try {
    // Parse request body
    const body = await request.json();
    const { email, name, source, resourceDownloaded, downloadLink } = body;
    
    // Validate email
    if (!email || !isValidEmail(email)) {
      return new Response(
        JSON.stringify({ error: 'Invalid email address' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    // Validate source
    const validSources = ['Blog', 'Analysis', 'Resource'];
    if (!source || !validSources.includes(source)) {
      return new Response(
        JSON.stringify({ error: 'Invalid source' }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      );
    }
    
    // Add lead to Notion
    const leadAdded = await addLead(
      email,
      name || '',
      source,
      resourceDownloaded || ''
    );
    
    if (!leadAdded) {
      console.error('Failed to add lead to Notion');
      // Continue anyway, don't fail the user experience
    }
    
    // Send appropriate email
    let emailSent = false;
    if (resourceDownloaded && source === 'Resource' && downloadLink) {
      emailSent = await sendResourceEmail(
        email,
        name || 'there',
        resourceDownloaded,
        downloadLink
      );
    } else {
      emailSent = await sendWelcomeEmail(email, name || 'there');
    }
    
    if (!emailSent) {
      console.error('Failed to send email');
      // Continue anyway, don't fail the user experience
    }
    
    return new Response(
      JSON.stringify({ 
        success: true,
        message: 'Successfully subscribed!'
      }),
      { 
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  } catch (error) {
    console.error('Error in subscribe endpoint:', error);
    return new Response(
      JSON.stringify({ 
        error: 'Internal server error',
        message: 'Failed to process subscription'
      }),
      { 
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
};

// Email validation helper
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}
