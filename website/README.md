# AgentCraft Website

A modern blog and resource hub built with Astro, integrated with Notion as a CMS for content management, analysis posts, and lead generation.

## 🚀 Features

- **📝 Blog System**: Publish and manage blog posts via Notion
- **📊 Analysis Hub**: Share in-depth market analysis and insights
- **📦 Resources Library**: Offer downloadable templates, guides, and tools
- **📧 Lead Generation**: Capture emails with gated content
- **🎨 Modern Design**: Responsive, accessible design with Tailwind CSS
- **⚡ Fast Performance**: Static site generation with Astro
- **🔄 Auto-Sync**: Scheduled builds to sync content from Notion

## 📋 Prerequisites

- Node.js 20 or higher
- npm or pnpm
- Notion account (for content management)
- Resend account (for email notifications)

## 🛠️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/CamelCod/agentcraft.git
   cd agentcraft/website
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   
   Fill in your environment variables:
   ```env
   NOTION_API_KEY=your_notion_integration_key
   NOTION_BLOG_DATABASE_ID=your_blog_database_id
   NOTION_ANALYSIS_DATABASE_ID=your_analysis_database_id
   NOTION_RESOURCES_DATABASE_ID=your_resources_database_id
   NOTION_LEADS_DATABASE_ID=your_leads_database_id
   RESEND_API_KEY=your_resend_api_key
   ```

4. **Set up Notion databases**
   
   Follow the instructions in [NOTION_SETUP.md](./NOTION_SETUP.md) to create and configure your Notion databases.

## 🏃 Running Locally

```bash
npm run dev
```

The site will be available at `http://localhost:4321`

## 🏗️ Building for Production

```bash
npm run build
```

The static site will be generated in the `dist/` directory.

## 👀 Preview Production Build

```bash
npm run preview
```

## 📝 Adding Content

### Blog Posts

1. Open your Notion Blog Posts database
2. Create a new page
3. Fill in all required properties:
   - Title
   - Slug (URL-friendly)
   - Status (set to "Published")
   - Published Date
   - Author
   - Tags
   - Excerpt
   - SEO Description
4. Write your content in the page
5. Rebuild the site to see changes

### Analysis Posts

1. Open your Notion Analysis database
2. Create a new page
3. Fill in all required properties
4. If creating a lead magnet:
   - Check "Lead Magnet"
   - Add a "Download URL"
5. Write your analysis content
6. Rebuild the site

### Resources

1. Open your Notion Resources database
2. Create a new page
3. Set the resource type
4. Add description and tags
5. If gating the resource:
   - Check "Gated"
   - Users will need to provide email to access
6. Add download link

## 🚀 Deployment

### GitHub Pages (Automated)

The site automatically deploys to GitHub Pages when you push to the main branch.

1. **Set up GitHub Secrets**
   
   Go to your repository settings → Secrets and variables → Actions, and add:
   - `NOTION_API_KEY`
   - `NOTION_BLOG_DATABASE_ID`
   - `NOTION_ANALYSIS_DATABASE_ID`
   - `NOTION_RESOURCES_DATABASE_ID`
   - `NOTION_LEADS_DATABASE_ID`
   - `RESEND_API_KEY`

2. **Enable GitHub Pages**
   
   Go to Settings → Pages → Source: GitHub Actions

3. **Push to main branch**
   ```bash
   git push origin main
   ```

The workflow will:
- Build the site with content from Notion
- Deploy to GitHub Pages
- Run every 6 hours to sync new content

### Manual Deployment

You can also trigger a deployment manually:
1. Go to Actions tab
2. Select "Deploy Blog to GitHub Pages"
3. Click "Run workflow"

## 🔧 Configuration

### Site Configuration

Edit `astro.config.mjs` to change:
- Site URL
- Base path
- Build options

### Styling

- Global styles: `src/styles/global.css`
- Tailwind config: `tailwind.config.mjs`
- Colors and theme: Modify Tailwind configuration

### Components

Reusable components are in `src/components/`:
- `Header.astro` - Site navigation
- `Footer.astro` - Site footer
- `BlogCard.astro` - Blog post card
- `AnalysisCard.astro` - Analysis post card
- `LeadCaptureForm.astro` - Email capture form
- `NewsletterSignup.astro` - Newsletter subscription

## 📧 Email Integration

The site uses Resend for email notifications:
- Welcome emails for new subscribers
- Download links for gated resources

Configure email templates in `src/lib/email.ts`.

## 🔍 SEO

The site includes:
- Meta tags for all pages
- Open Graph tags
- Twitter Cards
- Sitemap (auto-generated)
- Robots.txt

## 🎨 Customization

### Colors

Edit `tailwind.config.mjs` to change the primary color scheme:
```js
colors: {
  primary: {
    // Your color palette
  }
}
```

### Layouts

Layouts are in `src/layouts/`:
- `BaseLayout.astro` - Base HTML structure
- `BlogPost.astro` - Blog post layout
- `AnalysisPost.astro` - Analysis post layout

## 🐛 Troubleshooting

### Content not showing
- Check that Notion databases are shared with your integration
- Verify database IDs in environment variables
- Ensure posts have Status = "Published"

### Build failures
- The site falls back to mock data if Notion is unavailable
- Check environment variables are set correctly
- Review GitHub Actions logs for specific errors

### Email not sending
- Verify RESEND_API_KEY is set
- Check Resend dashboard for errors
- The site will continue to work even if emails fail

## 📚 Tech Stack

- **Framework**: [Astro](https://astro.build)
- **Styling**: [Tailwind CSS](https://tailwindcss.com)
- **CMS**: [Notion](https://notion.so)
- **Email**: [Resend](https://resend.com)
- **Hosting**: GitHub Pages
- **Language**: TypeScript

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available for use and modification.

## 🔗 Links

- [Live Site](https://camelcod.github.io/agentcraft)
- [GitHub Repository](https://github.com/CamelCod/agentcraft)
- [Notion Setup Guide](./NOTION_SETUP.md)

## 💬 Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review the Notion setup guide

---

Built with ❤️ using Astro and Notion
