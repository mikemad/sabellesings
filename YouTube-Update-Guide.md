# 🎵 YouTube Video Update Guide for Sabelle's Website

This guide explains how to easily update the YouTube videos displayed on your website using the helper tool.

## 📁 Files You Need

- `youtube-helper.html` - The helper tool (open this in your browser)
- `index.html` - Your main website file (where you'll paste the generated code)

## 🚀 Quick Update Process

### Step 1: Open the Helper Tool
1. Double-click `youtube-helper.html` to open it in your browser
2. The tool will load with your current videos already filled in

### Step 2: Update Your Videos
1. **To replace a video:** Change the URL and title in any existing field
2. **To add new videos:** Click "+ Add Another Video" 
3. **To remove videos:** Click "Remove" next to any video (must keep at least one)
4. **To reorder videos:** The first video in the list will appear first on your website

### Step 3: Generate the Code
1. Click "🚀 Generate HTML Code"
2. The tool will create the HTML code and show a preview
3. Click "📋 Copy to Clipboard" to copy the generated code

### Step 4: Update Your Website
1. Open `index.html` in your code editor
2. Find the YouTube section (around line 175-210)
3. Look for `<div class="video-grid">` and select everything until `</div>`
4. Replace the selected content with your copied code
5. Save the file

### Step 5: Test Your Changes
1. Open `index.html` in your browser to preview
2. Check that all videos load correctly
3. Upload your updated `index.html` to your web server

## 📋 Getting YouTube Video URLs

### From YouTube Studio (Recommended):
1. Go to [YouTube Studio](https://studio.youtube.com)
2. Click "Content" in the left sidebar
3. Find your video and click on it
4. Copy the "Watch page URL" from the details

### From YouTube Channel:
1. Go to your channel: https://www.youtube.com/@Sabellesings
2. Click on any video
3. Copy the URL from your browser's address bar

## 💡 Pro Tips

### Video Selection Strategy:
- **First 2-3 videos:** Your newest/most important releases
- **Middle videos:** Popular favorites or recent performances  
- **Last videos:** Older classics that showcase your range

### Best Practices:
- **Update monthly** or when you release new content
- **Keep 6 videos** for the best visual layout
- **Use descriptive titles** that match your actual video titles
- **Test on mobile** - videos should look good on phones too

### Backup Your Work:
- Before making changes, save a copy of your current `index.html`
- Keep a list of your current video URLs somewhere safe

## 🔧 Troubleshooting

### "Invalid YouTube URL" Error:
- Make sure you're using the full YouTube URL (starts with `https://www.youtube.com/watch?v=`)
- Don't use shortened URLs (youtu.be) - convert them to full URLs first

### Videos Not Loading:
- Check that the video is public (not private or unlisted)
- Verify the URL is correct by testing it in a new browser tab

### Layout Issues:
- The tool is designed for exactly 6 videos for the best layout
- If you use fewer videos, they'll be larger
- If you use more videos, consider removing older ones

## 📞 Need Help?

If you run into any issues:
1. Double-check that you followed each step
2. Make sure your video URLs are correct and public
3. Test the helper tool with just one video first
4. Keep a backup of your working `index.html` file

## 🎯 Quick Reference

**Helper Tool Location:** `youtube-helper.html`
**Website File:** `index.html` 
**Section to Replace:** Lines ~175-210 (the `<div class="video-grid">` section)
**Recommended Update Frequency:** Monthly or after new releases

---

*This guide was created to make updating your YouTube videos as simple as possible. The helper tool does all the technical work - you just need to provide the video URLs and titles!*
