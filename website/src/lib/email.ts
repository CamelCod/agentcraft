import { Resend } from 'resend';

// Get sender email from environment or use default
const getSenderEmail = () => {
  const fromDomain = import.meta.env.FROM_EMAIL_DOMAIN || 'agentcraft.dev';
  return `AgentCraft <noreply@${fromDomain}>`;
};

/**
 * Send welcome email to new subscriber
 */
export async function sendWelcomeEmail(email: string, name: string): Promise<boolean> {
  try {
    if (!import.meta.env.RESEND_API_KEY) {
      console.warn('RESEND_API_KEY not set, skipping email send');
      return true; // Return true in development
    }

    const resend = new Resend(import.meta.env.RESEND_API_KEY);
    await resend.emails.send({
      from: getSenderEmail(),
      to: email,
      subject: 'Welcome to AgentCraft!',
      html: getWelcomeEmailTemplate(name)
    });

    return true;
  } catch (error) {
    console.error('Error sending welcome email:', error);
    return false;
  }
}

/**
 * Send resource download email
 */
export async function sendResourceEmail(
  email: string, 
  name: string, 
  resourceTitle: string, 
  downloadLink: string
): Promise<boolean> {
  try {
    if (!import.meta.env.RESEND_API_KEY) {
      console.warn('RESEND_API_KEY not set, skipping email send');
      return true; // Return true in development
    }

    const resend = new Resend(import.meta.env.RESEND_API_KEY);
    await resend.emails.send({
      from: getSenderEmail(),
      to: email,
      subject: `Your ${resourceTitle} is ready!`,
      html: getResourceEmailTemplate(name, resourceTitle, downloadLink)
    });

    return true;
  } catch (error) {
    console.error('Error sending resource email:', error);
    return false;
  }
}

/**
 * Welcome email HTML template
 */
function getWelcomeEmailTemplate(name: string): string {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
          }
          .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
          }
          .content {
            background: #f9fafb;
            padding: 30px 20px;
            border-radius: 0 0 10px 10px;
          }
          .button {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
          }
          .footer {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 30px;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🤖 Welcome to AgentCraft!</h1>
        </div>
        <div class="content">
          <p>Hi ${name || 'there'},</p>
          <p>Thanks for joining the AgentCraft community! We're excited to have you on board.</p>
          <p>AgentCraft is your hub for intelligent agents and automation tools. Here's what you can expect:</p>
          <ul>
            <li>📚 In-depth tutorials and guides</li>
            <li>📊 Market analysis and insights</li>
            <li>🔧 Practical templates and tools</li>
            <li>💡 Industry best practices</li>
          </ul>
          <p style="text-align: center;">
            <a href="https://camelcod.github.io/agentcraft" class="button">Explore AgentCraft</a>
          </p>
          <p>Stay tuned for our latest content and resources!</p>
          <p>Best regards,<br>The AgentCraft Team</p>
        </div>
        <div class="footer">
          <p>You received this email because you subscribed to AgentCraft updates.</p>
        </div>
      </body>
    </html>
  `;
}

/**
 * Resource download email HTML template
 */
function getResourceEmailTemplate(name: string, resourceTitle: string, downloadLink: string): string {
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
          }
          .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
            border-radius: 10px 10px 0 0;
          }
          .content {
            background: #f9fafb;
            padding: 30px 20px;
            border-radius: 0 0 10px 10px;
          }
          .button {
            display: inline-block;
            background: #10b981;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            margin: 20px 0;
            font-weight: 600;
          }
          .footer {
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            margin-top: 30px;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>📥 Your Resource is Ready!</h1>
        </div>
        <div class="content">
          <p>Hi ${name || 'there'},</p>
          <p>Thank you for your interest in <strong>${resourceTitle}</strong>!</p>
          <p>Your download is ready. Click the button below to access your resource:</p>
          <p style="text-align: center;">
            <a href="${downloadLink}" class="button">Download Now</a>
          </p>
          <p>We hope you find this resource valuable. If you have any questions or feedback, feel free to reach out!</p>
          <p>Looking for more resources? Visit our <a href="https://camelcod.github.io/agentcraft/resources">Resources page</a>.</p>
          <p>Best regards,<br>The AgentCraft Team</p>
        </div>
        <div class="footer">
          <p>You received this email because you requested "${resourceTitle}" from AgentCraft.</p>
        </div>
      </body>
    </html>
  `;
}
