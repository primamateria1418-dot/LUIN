"""
LUIN Platform-Specific Demographic & Engagement Prompts
Tailored prompt templates for Twitter, LinkedIn, Instagram, and Facebook
based on user demographics, engagement models, and content best practices.
"""

PLATFORM_PROFILES = {
    "twitter": {
        "name": "X (Twitter)",
        "max_chars": 280,
        "demographic": "Ages 18-49, tech-savvy, news-oriented, politically engaged",
        "engagement_model": "Real-time conversation, retweets, quotes, threads",
        "tone": "Punchy, direct, witty, conversational, thread-style",
        "hashtag_strategy": "2-3 relevant hashtags, mix of broad and niche",
        "best_posting_times": "7-9 AM, 12-2 PM, 5-7 PM (local time)",
        "content_format": "Threads for deep dives, single posts for quick hits, polls for engagement",
        "prompt_template": """Generate {count} {content_type} posts for {platform} targeting {audience}.
Tone: {tone}
Length: Max {max_chars} characters
Hashtags: {hashtag_strategy}
Structure: {content_format}
Brand Voice: {brand_voice}
Key Message: {key_message}
Call to Action: {cta}
Output each post on a new line with hashtags included.
""",
    },
    "linkedin": {
        "name": "LinkedIn",
        "max_chars": 3000,
        "demographic": "Ages 25-54, professionals, B2B decision-makers, industry leaders",
        "engagement_model": "Thought leadership, industry insights, professional networking",
        "tone": "Professional, authoritative, insightful, data-driven, thought-leadership",
        "hashtag_strategy": "3-5 professional hashtags, industry-specific, broad reach tags",
        "best_posting_times": "8-10 AM, 12-1 PM, 5-6 PM (Tuesday-Thursday)",
        "content_format": "Long-form posts, carousels, articles, video snippets",
        "prompt_template": """Generate {count} {content_type} posts for {platform} targeting {audience}.
Tone: {tone}
Length: Professional, up to {max_chars} characters
Hashtags: {hashtag_strategy}
Structure: {content_format}
Brand Voice: {brand_voice}
Key Message: {key_message}
Call to Action: {cta}
Include professional insights and industry context. Output each post on a new line.
""",
    },
    "instagram": {
        "name": "Instagram",
        "max_chars": 2200,
        "demographic": "Ages 18-34, visual-first, lifestyle, entertainment, shopping",
        "engagement_model": "Visual storytelling, reels, carousels, stories, DMs",
        "tone": "Visual-first, emoji-friendly, aspirational, community-focused",
        "hashtag_strategy": "8-15 hashtags, mix of niche, broad, and branded tags",
        "best_posting_times": "11 AM-1 PM, 7-9 PM (weekends higher engagement)",
        "content_format": "Carousel posts, reels scripts, story sequences, high-quality visuals",
        "prompt_template": """Generate {count} {content_type} posts for {platform} targeting {audience}.
Tone: {tone}
Length: Engaging caption up to {max_chars} characters
Hashtags: {hashtag_strategy}
Structure: {content_format}
Brand Voice: {brand_voice}
Key Message: {key_message}
Call to Action: {cta}
Include emoji suggestions and visual direction. Output each post on a new line.
""",
    },
    "facebook": {
        "name": "Facebook",
        "max_chars": 63206,
        "demographic": "Ages 25-55, community-oriented, family, local groups, diverse interests",
        "engagement_model": "Community building, group discussions, event promotion, shareable content",
        "tone": "Conversational, community-focused, informative, relationship-driven",
        "hashtag_strategy": "0-3 hashtags, focus on community tags and event tags",
        "best_posting_times": "1-4 PM, 7-9 PM (weekdays), weekends for events",
        "content_format": "Long-form posts, event pages, group discussions, photo albums, videos",
        "prompt_template": """Generate {count} {content_type} posts for {platform} targeting {audience}.
Tone: {tone}
Length: Community-focused, up to {max_chars} characters
Hashtags: {hashtag_strategy}
Structure: {content_format}
Brand Voice: {brand_voice}
Key Message: {key_message}
Call to Action: {cta}
Include community engagement prompts and shareable elements. Output each post on a new line.
""",
    },
}

def get_platform_profile(platform: str) -> dict:
    """Get platform-specific demographic and engagement profile."""
    return PLATFORM_PROFILES.get(platform.lower(), PLATFORM_PROFILES["twitter"])

def generate_platform_prompt(platform: str, campaign_data: dict) -> str:
    """Generate a tailored prompt for a specific platform."""
    profile = get_platform_profile(platform)
    template = profile["prompt_template"]
    
    # Replace placeholders with campaign data
    for key, value in campaign_data.items():
        template = template.replace(f"{{{key}}}", str(value))
    
    return template
