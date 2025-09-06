#!/usr/bin/env python3
"""
Demo script to showcase NeetiManthan functionality
"""
import asyncio
import httpx
import csv
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000/api/v1"

async def wait_for_api():
    """Wait for API to be ready"""
    print("🔍 Waiting for API to be ready...")
    for _ in range(30):  # Wait up to 30 seconds
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{API_BASE}/health")
                if response.status_code == 200:
                    print("✅ API is ready!")
                    return True
        except:
            pass
        await asyncio.sleep(1)
    
    print("❌ API is not responding. Please check if services are running.")
    return False

async def create_draft():
    """Create a draft document"""
    print("\n📄 Creating draft document...")
    
    # Read sample draft
    draft_path = Path("data/sample_draft.txt")
    if not draft_path.exists():
        print("❌ Sample draft file not found!")
        return None
    
    with open(draft_path, 'r', encoding='utf-8') as f:
        draft_content = f.read()
    
    draft_data = {
        "title": "Companies (Amendment) Rules, 2024",
        "content": draft_content
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE}/drafts", json=draft_data)
            if response.status_code == 200:
                draft = response.json()
                print(f"✅ Draft created with ID: {draft['id']}")
                print(f"   Title: {draft['title']}")
                return draft['id']
            else:
                print(f"❌ Failed to create draft: {response.status_code}")
                print(response.text)
                return None
        except Exception as e:
            print(f"❌ Error creating draft: {e}")
            return None

async def upload_comments(draft_id):
    """Upload sample comments"""
    print(f"\n💬 Uploading comments for draft {draft_id}...")
    
    # Read sample comments
    comments_path = Path("data/sample_comments.csv")
    if not comments_path.exists():
        print("❌ Sample comments file not found!")
        return []
    
    comments = []
    with open(comments_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            comments.append({
                "text": row['text'],
                "meta": {
                    "user_type": row['user_type'],
                    "organization": row['organization'],
                    "state": row['state']
                }
            })
    
    # Upload in bulk
    bulk_data = {
        "draft_id": draft_id,
        "comments": comments
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{API_BASE}/comments/bulk", json=bulk_data)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Uploaded {len(comments)} comments")
                return result.get('ids', [])
            else:
                print(f"❌ Failed to upload comments: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"❌ Error uploading comments: {e}")
            return []

async def wait_for_processing(comment_ids, max_wait=120):
    """Wait for comments to be processed"""
    print(f"\n⏳ Waiting for {len(comment_ids)} comments to be processed...")
    
    start_time = time.time()
    processed_count = 0
    
    while time.time() - start_time < max_wait:
        async with httpx.AsyncClient() as client:
            try:
                # Check a few sample comments
                sample_ids = comment_ids[:5]
                current_processed = 0
                
                for comment_id in sample_ids:
                    response = await client.get(f"{API_BASE}/comments/{comment_id}")
                    if response.status_code == 200:
                        comment = response.json()
                        if comment.get('predictions') or comment.get('summaries'):
                            current_processed += 1
                
                if current_processed > processed_count:
                    processed_count = current_processed
                    print(f"   📊 {processed_count}/{len(sample_ids)} sample comments processed...")
                
                if current_processed == len(sample_ids):
                    print("✅ Comments processing completed!")
                    return True
                
            except Exception as e:
                print(f"   ⚠️  Error checking processing status: {e}")
        
        await asyncio.sleep(5)
    
    print(f"⏱️  Processing timeout. {processed_count} comments processed so far.")
    return processed_count > 0

async def show_analytics(draft_id):
    """Display analytics for the draft"""
    print(f"\n📊 Analytics for draft {draft_id}:")
    
    async with httpx.AsyncClient() as client:
        try:
            # Get summary
            response = await client.get(f"{API_BASE}/analytics/drafts/{draft_id}/summary")
            if response.status_code == 200:
                summary = response.json()
                
                print(f"   📝 Total Comments: {summary.get('total_comments', 0)}")
                print(f"   ✅ Processed: {summary.get('processed_comments', 0)}")
                print(f"   📈 Processing Rate: {summary.get('processing_rate', 0):.1f}%")
                print(f"   🎯 Average Confidence: {summary.get('average_confidence', 0):.2f}")
                
                # Sentiment distribution
                sentiment_dist = summary.get('sentiment_distribution', {})
                if sentiment_dist:
                    print("   😊 Sentiment Distribution:")
                    for sentiment, count in sentiment_dist.items():
                        print(f"      • {sentiment}: {count}")
                
                # Stance distribution
                stance_dist = summary.get('stance_distribution', {})
                if stance_dist:
                    print("   🎭 Stance Distribution:")
                    for stance, count in stance_dist.items():
                        print(f"      • {stance}: {count}")
                
                # Language distribution
                lang_dist = summary.get('language_distribution', {})
                if lang_dist:
                    print("   🌐 Language Distribution:")
                    for lang, count in lang_dist.items():
                        print(f"      • {lang}: {count}")
            
            # Get clause analysis
            response = await client.get(f"{API_BASE}/analytics/drafts/{draft_id}/clause-analysis")
            if response.status_code == 200:
                clause_analysis = response.json()
                if clause_analysis:
                    print("   📋 Top Clause Mentions:")
                    sorted_clauses = sorted(
                        clause_analysis.items(), 
                        key=lambda x: x[1].get('total_comments', 0), 
                        reverse=True
                    )[:5]
                    
                    for clause_ref, data in sorted_clauses:
                        print(f"      • {clause_ref}: {data.get('total_comments', 0)} comments")
            
            # Get keywords
            response = await client.get(f"{API_BASE}/analytics/drafts/{draft_id}/keywords?limit=10")
            if response.status_code == 200:
                keywords = response.json()
                if keywords:
                    print("   🔑 Top Keywords:")
                    for kw in keywords[:10]:
                        print(f"      • {kw['term']}: {kw['weight']:.3f}")
                        
        except Exception as e:
            print(f"❌ Error fetching analytics: {e}")

async def export_results(draft_id):
    """Export analysis results"""
    print(f"\n📤 Exporting results for draft {draft_id}...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/analytics/drafts/{draft_id}/export?format=csv")
            if response.status_code == 200:
                # Save to file
                export_path = Path(f"data/export_draft_{draft_id}.csv")
                with open(export_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Results exported to {export_path}")
            else:
                print(f"❌ Failed to export: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error exporting: {e}")

async def main():
    """Main demo function"""
    print("🎯 NeetiManthan Demo Script")
    print("=" * 50)
    
    # Wait for API
    if not await wait_for_api():
        return
    
    # Create draft
    draft_id = await create_draft()
    if not draft_id:
        return
    
    # Upload comments
    comment_ids = await upload_comments(draft_id)
    if not comment_ids:
        return
    
    # Wait for processing
    if await wait_for_processing(comment_ids):
        # Show analytics
        await show_analytics(draft_id)
        
        # Export results
        await export_results(draft_id)
    
    print("\n🎉 Demo completed!")
    print(f"   • Draft ID: {draft_id}")
    print(f"   • Comments uploaded: {len(comment_ids)}")
    print("   • Check the API docs at: http://localhost:8000/docs")
    print("   • View exported results in data/ folder")

if __name__ == "__main__":
    asyncio.run(main())
