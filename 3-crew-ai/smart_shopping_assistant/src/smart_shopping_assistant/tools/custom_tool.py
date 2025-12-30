"""
Smart Shopping Assistant Tools

This module contains tools for product search, product details, reviews, and sentiment analysis.
All tools interact with the Real-Time Product Search API (via RapidAPI) except analyze_sentiment
which performs local processing.

Tools:
    - SearchProductsTool: Search for products across multiple retailers
    - GetProductDetailsTool: Get comprehensive details for a specific product
    - GetProductReviewsTool: Fetch customer reviews for a product
    - AnalyzeSentimentTool: Analyze review text to extract sentiment and insights
"""

import os
import re
from collections import Counter
from typing import Any, List, Optional, Type

import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


# =============================================================================
# RapidAPI Configuration
# =============================================================================

RAPIDAPI_HOST = "real-time-product-search.p.rapidapi.com"
RAPIDAPI_BASE_URL = f"https://{RAPIDAPI_HOST}"

# Valid sort options for the APIs
VALID_PRODUCT_SORT_OPTIONS = {"BEST_MATCH", "LOWEST_PRICE", "HIGHEST_PRICE", "TOP_RATED"}
VALID_REVIEWS_SORT_OPTIONS = {"MOST_RELEVANT", "DATE"}


def get_rapidapi_headers() -> dict:
    """Get headers for RapidAPI requests."""
    api_key = os.getenv("RAPID_API_KEY")
    if not api_key:
        raise ValueError("RAPID_API_KEY environment variable not set")
    return {
        "x-rapidapi-key": api_key,
        "x-rapidapi-host": RAPIDAPI_HOST
    }


# =============================================================================
# Tool 1: Search Products
# =============================================================================

class SearchProductsInput(BaseModel):
    """Input schema for SearchProductsTool."""

    query: str = Field(
        ...,
        description="Search keywords (e.g., 'gaming laptop 16GB RAM', 'Sony headphones')"
    )
    min_price: Optional[float] = Field(
        default=None,
        description="Minimum price filter in USD"
    )
    max_price: Optional[float] = Field(
        default=None,
        description="Maximum price filter in USD"
    )
    sort_by: str = Field(
        default="BEST_MATCH",
        description="Sort order: BEST_MATCH, LOWEST_PRICE, HIGHEST_PRICE, or TOP_RATED"
    )
    product_condition: str = Field(
        default="ANY",
        description="Product condition: ANY, NEW, USED, or REFURBISHED"
    )
    country: str = Field(
        default="us",
        description="Country code for localized results (default: us)"
    )
    language: str = Field(
        default="en",
        description="Language code (default: en)"
    )
    limit: int = Field(
        default=10,
        description="Number of results to return (default: 10)"
    )
    page: int = Field(
        default=1,
        description="Page number for pagination (default: 1)"
    )


class SearchProductsTool(BaseTool):
    """
    Search for products across multiple retailers using Real-Time Product Search API v2.
    
    Returns products with prices, ratings, and offers from different stores including
    Amazon, Best Buy, Walmart, and more.
    """
    
    name: str = "search_products"
    description: str = (
        "Search for products across multiple retailers. Returns products with prices, "
        "ratings, and offers from different stores. Use this tool when users want to "
        "find products, compare prices, or discover options within a budget. "
        "Parameters: query (required), min_price, max_price, sort_by (BEST_MATCH, "
        "LOWEST_PRICE, HIGHEST_PRICE, TOP_RATED), product_condition (ANY, NEW, USED, "
        "REFURBISHED), limit (number of results)."
    )
    args_schema: Type[BaseModel] = SearchProductsInput

    def _run(
        self,
        query: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "BEST_MATCH",
        product_condition: str = "ANY",
        country: str = "us",
        language: str = "en",
        limit: int = 10,
        page: int = 1
    ) -> dict:
        """Execute the product search."""
        
        # Validate and normalize sort_by parameter
        sort_mapping = {
            "REVIEW_SCORE": "TOP_RATED",
            "RATING": "TOP_RATED",
            "RELEVANCE": "BEST_MATCH",
        }
        normalized_sort = sort_mapping.get(sort_by.upper(), sort_by.upper())
        if normalized_sort not in VALID_PRODUCT_SORT_OPTIONS:
            normalized_sort = "BEST_MATCH"
        
        params = {
            "q": query,
            "country": country,
            "language": language,
            "limit": str(limit),
            "page": str(page),
            "sort_by": normalized_sort,
            "product_condition": product_condition
        }
        
        if min_price is not None:
            params["min_price"] = str(int(min_price))
        if max_price is not None:
            params["max_price"] = str(int(max_price))
        
        try:
            response = requests.get(
                f"{RAPIDAPI_BASE_URL}/search-v2",
                headers=get_rapidapi_headers(),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "FAILED"}


# =============================================================================
# Tool 2: Get Product Details
# =============================================================================

class GetProductDetailsInput(BaseModel):
    """Input schema for GetProductDetailsTool."""

    product_id: str = Field(
        ...,
        description="Product ID from search_products results (long string like 'catalogid:123...')"
    )
    country: str = Field(
        default="us",
        description="Country code for localized pricing (default: us)"
    )
    language: str = Field(
        default="en",
        description="Language code (default: en)"
    )


class GetProductDetailsTool(BaseTool):
    """
    Get comprehensive details and specifications for a specific product.
    
    Returns full product details including specifications, images, ratings,
    and all available prices from different retailers.
    """
    
    name: str = "get_product_details"
    description: str = (
        "Get comprehensive details and specifications for a specific product. "
        "Use this tool when you need full technical specifications, complete price "
        "comparison across all stores, or detailed product information. "
        "Requires product_id from search_products results."
    )
    args_schema: Type[BaseModel] = GetProductDetailsInput

    def _run(
        self,
        product_id: str,
        country: str = "us",
        language: str = "en"
    ) -> dict:
        """Execute the product details lookup."""
        
        params = {
            "product_id": product_id,
            "country": country,
            "language": language
        }
        
        try:
            response = requests.get(
                f"{RAPIDAPI_BASE_URL}/product-details-v2",
                headers=get_rapidapi_headers(),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "FAILED"}


# =============================================================================
# Tool 3: Get Product Reviews
# =============================================================================

class GetProductReviewsInput(BaseModel):
    """Input schema for GetProductReviewsTool."""

    product_id: str = Field(
        ...,
        description=(
            "Product ID from search_products results. "
            "MUST be the exact ID (long string like 'catalogid:123...'). "
            "Do NOT make up product IDs - they will return empty results."
        )
    )
    country: str = Field(
        default="us",
        description="Country code for localized reviews (default: us)"
    )
    language: str = Field(
        default="en",
        description="Language code (default: en)"
    )
    limit: int = Field(
        default=10,
        description="Number of reviews to fetch (default: 10)"
    )
    sort_by: str = Field(
        default="MOST_RELEVANT",
        description="Sort order: MOST_RELEVANT or DATE (default: MOST_RELEVANT)"
    )


class GetProductReviewsTool(BaseTool):
    """
    Fetch customer reviews and ratings for a specific product.
    
    Returns individual reviews with ratings, text, metadata, and overall rating breakdown.
    """
    
    name: str = "get_product_reviews"
    description: str = (
        "Fetch customer reviews and ratings for a specific product. "
        "Returns individual reviews with ratings, text, and metadata. "
        "Use this tool when users want to know what customers say about a product. "
        "Requires product_id from search_products results (long string starting with 'catalogid:')."
    )
    args_schema: Type[BaseModel] = GetProductReviewsInput

    def _run(
        self,
        product_id: str,
        country: str = "us",
        language: str = "en",
        limit: int = 10,
        sort_by: str = "MOST_RELEVANT"
    ) -> dict:
        """Execute the product reviews fetch."""
        
        # Validate and normalize sort_by parameter
        sort_mapping = {
            "NEWEST": "DATE",
            "RECENT": "DATE",
            "DATE_DESC": "DATE",
            "HIGHEST_RATING": "MOST_RELEVANT",
            "LOWEST_RATING": "MOST_RELEVANT",
            "BEST": "MOST_RELEVANT",
        }
        normalized_sort = sort_mapping.get(sort_by.upper(), sort_by.upper())
        if normalized_sort not in VALID_REVIEWS_SORT_OPTIONS:
            normalized_sort = "MOST_RELEVANT"
        
        params = {
            "product_id": product_id,
            "country": country,
            "language": language,
            "limit": str(limit),
            "sort_by": normalized_sort
        }
        
        try:
            response = requests.get(
                f"{RAPIDAPI_BASE_URL}/product-reviews-v2",
                headers=get_rapidapi_headers(),
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e), "status": "FAILED"}


# =============================================================================
# Tool 4: Analyze Sentiment
# =============================================================================

class AnalyzeSentimentInput(BaseModel):
    """Input schema for AnalyzeSentimentTool."""

    reviews: List[dict] = Field(
        default=[],
        description="Array of review objects from get_product_reviews"
    )
    focus_area: Optional[str] = Field(
        default=None,
        description="Optional specific aspect to analyze (e.g., 'battery', 'durability', 'comfort')"
    )


class AnalyzeSentimentTool(BaseTool):
    """
    Analyze review text to extract sentiment, themes, pros, and cons.
    
    This is a local processing tool - no external API call required.
    Processes reviews to identify common patterns, sentiment, and concerns.
    """
    
    name: str = "analyze_sentiment"
    description: str = (
        "Analyze review text to extract sentiment, themes, pros, and cons. "
        "Use this tool after fetching reviews with get_product_reviews. "
        "Returns overall sentiment (positive/negative/mixed/neutral), sentiment score, "
        "common pros and cons, themes, red flags, and a recommendation. "
        "Can optionally focus on specific aspects like 'battery', 'durability', etc."
    )
    args_schema: Type[BaseModel] = AnalyzeSentimentInput

    def _run(
        self,
        reviews: List[dict] = None,
        focus_area: Optional[str] = None
    ) -> dict:
        """Execute the sentiment analysis."""
        
        # Handle None or empty reviews gracefully
        if reviews is None:
            reviews = []
        
        if not reviews:
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.0,
                "total_analyzed": 0,
                "pros": [],
                "cons": [],
                "common_themes": [],
                "notable_reviews": [],
                "red_flags": [],
                "recommendation": "No reviews available to analyze."
            }
        
        # Positive and negative keyword patterns
        positive_keywords = [
            "great", "excellent", "amazing", "love", "perfect", "best", "awesome",
            "fantastic", "wonderful", "quality", "comfortable", "recommend", "worth",
            "happy", "satisfied", "impressive", "solid", "reliable", "easy"
        ]
        negative_keywords = [
            "poor", "bad", "terrible", "worst", "broken", "disappointed", "waste",
            "cheap", "defective", "problem", "issue", "fail", "return", "refund",
            "uncomfortable", "unreliable", "slow", "loud", "flimsy", "avoid"
        ]
        
        # Categorize reviews by rating
        positive_reviews = []  # 4-5 stars
        neutral_reviews = []   # 3 stars
        negative_reviews = []  # 1-2 stars
        
        all_text = []
        ratings = []
        
        for review in reviews:
            rating = review.get("rating") or review.get("review_rating")
            content = review.get("review_text") or review.get("content") or review.get("review_content") or ""
            title = review.get("review_title") or review.get("title") or ""
            
            full_text = f"{title} {content}".lower()
            all_text.append(full_text)
            
            if rating:
                ratings.append(rating)
                if rating >= 4:
                    positive_reviews.append(review)
                elif rating == 3:
                    neutral_reviews.append(review)
                else:
                    negative_reviews.append(review)
        
        # Calculate sentiment score
        avg_rating = None
        if ratings:
            avg_rating = sum(ratings) / len(ratings)
            sentiment_score = (avg_rating - 3) / 2  # Convert 1-5 scale to -1 to 1
        else:
            sentiment_score = 0.0
        
        # Determine overall sentiment
        if sentiment_score > 0.3:
            overall_sentiment = "positive"
        elif sentiment_score < -0.3:
            overall_sentiment = "negative"
        elif len(positive_reviews) > 0 and len(negative_reviews) > 0:
            overall_sentiment = "mixed"
        else:
            overall_sentiment = "neutral"
        
        # Extract pros and cons from review text
        combined_text = " ".join(all_text)
        
        pros = []
        cons = []
        
        for keyword in positive_keywords:
            if keyword in combined_text:
                count = combined_text.count(keyword)
                if count >= 2:  # Only include if mentioned multiple times
                    pros.append(keyword)
        
        for keyword in negative_keywords:
            if keyword in combined_text:
                count = combined_text.count(keyword)
                if count >= 2:
                    cons.append(keyword)
        
        # Filter by focus area if specified
        if focus_area:
            focus_lower = focus_area.lower()
            relevant_text = [t for t in all_text if focus_lower in t]
            if relevant_text:
                combined_text = " ".join(relevant_text)
        
        # Identify common themes (simple word frequency)
        words = re.findall(r'\b[a-z]{4,}\b', combined_text)
        word_counts = Counter(words)
        # Remove common stop words
        stop_words = {
            "this", "that", "with", "have", "from", "they", "been", "were",
            "will", "would", "could", "should", "about", "into", "than",
            "them", "then", "these", "very", "just", "your", "some", "more",
            "also", "what", "when"
        }
        common_themes = [
            word for word, count in word_counts.most_common(20)
            if word not in stop_words and count >= 3
        ][:10]
        
        # Identify red flags (serious concerns)
        red_flag_patterns = [
            "defective", "broke", "broken", "dangerous", "safety",
            "recall", "fire", "burn", "shock", "injury"
        ]
        red_flags = [pattern for pattern in red_flag_patterns if pattern in combined_text]
        
        # Find notable reviews (high helpful votes or detailed)
        notable_reviews = []
        for review in reviews[:5]:  # Check first 5 reviews
            helpful = review.get("review_helpful_count") or review.get("helpful_votes") or 0
            content = review.get("review_text") or review.get("content") or ""
            if helpful > 10 or len(content) > 200:
                notable_reviews.append({
                    "title": review.get("review_title") or review.get("title") or "No title",
                    "rating": review.get("rating") or review.get("review_rating"),
                    "helpful_votes": helpful,
                    "snippet": content[:150] + "..." if len(content) > 150 else content
                })
        
        # Generate recommendation
        if overall_sentiment == "positive":
            recommendation = (
                f"Generally well-reviewed with {len(positive_reviews)} positive reviews. "
                f"Most customers are satisfied with this product."
            )
        elif overall_sentiment == "negative":
            recommendation = (
                f"Caution advised - {len(negative_reviews)} negative reviews. "
                f"Common complaints include: {', '.join(cons[:3]) if cons else 'various issues'}."
            )
        elif overall_sentiment == "mixed":
            recommendation = (
                f"Mixed reviews ({len(positive_reviews)} positive, {len(negative_reviews)} negative). "
                f"Consider both pros and cons carefully before purchasing."
            )
        else:
            recommendation = "Insufficient data to make a strong recommendation."
        
        return {
            "overall_sentiment": overall_sentiment,
            "sentiment_score": round(sentiment_score, 2),
            "total_analyzed": len(reviews),
            "rating_breakdown": {
                "positive": len(positive_reviews),
                "neutral": len(neutral_reviews),
                "negative": len(negative_reviews)
            },
            "average_rating": round(avg_rating, 1) if avg_rating else None,
            "pros": pros[:5],
            "cons": cons[:5],
            "common_themes": common_themes,
            "notable_reviews": notable_reviews[:3],
            "red_flags": red_flags,
            "recommendation": recommendation
        }


# =============================================================================
# Tool Instances for Easy Import
# =============================================================================

# Create tool instances that can be directly imported and used
search_products_tool = SearchProductsTool()
get_product_details_tool = GetProductDetailsTool()
get_product_reviews_tool = GetProductReviewsTool()
analyze_sentiment_tool = AnalyzeSentimentTool()
