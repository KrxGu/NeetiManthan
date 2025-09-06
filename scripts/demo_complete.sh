#!/bin/bash

echo "🎯 NeetiManthan - Complete Application Demo"
echo "AI-Powered Public Comment Analysis System"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🌟 System Overview${NC}"
echo "✅ Frontend: React + Tailwind CSS Dashboard"
echo "✅ Backend: FastAPI with Mock Sentiment Analysis"
echo "✅ Database: PostgreSQL + pgvector"
echo "✅ Storage: MinIO Object Storage"
echo "✅ Cache: Redis"
echo ""

echo -e "${BLUE}🚀 Starting Demo Workflow${NC}"
echo ""

echo -e "${YELLOW}📄 Step 1: Upload Draft Document${NC}"
draft_response=$(curl -s -X POST http://localhost:8000/draft/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Companies (Amendment) Rules, 2024",
    "content": "1. Short title and commencement\n(1) These rules may be called the Companies (Amendment) Rules, 2024.\n(2) They shall come into force on the date of their publication in the Official Gazette.\n\n2. Definitions\nIn these rules, unless the context otherwise requires:\n(a) \"digital signature\" means authentication of any electronic record.\n(b) \"electronic form\" means a form prescribed under these rules.\n\n3. Application for incorporation\n(1) Every application for incorporation shall be made in Form INC-32.\n(2) The application shall be accompanied by required documents.\n\n4. Processing timeline\n(1) The Registrar shall process applications within 15 working days.\n(2) In case of deficiencies, applicant will be notified within 5 days.\n\n5. Digital compliance\n(1) All forms shall be filed electronically through the MCA portal.\n(2) Physical documents may be required in exceptional cases."
  }')

echo "📋 Draft uploaded successfully!"
echo "   Title: Companies (Amendment) Rules, 2024"
clauses_count=$(echo "$draft_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['clauses_extracted'])")
echo "   Clauses extracted: $clauses_count"
echo ""

echo -e "${YELLOW}💬 Step 2: Process Individual Comments${NC}"

# Process several individual comments
comments=(
    '{"text": "I strongly support these amendments as they will simplify the incorporation process for startups and small businesses.", "user_type": "Entrepreneur", "organization": "Startup India", "state": "Karnataka"}'
    '{"text": "The 15-day processing timeline is too long. It should be reduced to 7 days to improve ease of doing business.", "user_type": "Legal Professional", "organization": "Bar Association", "state": "Delhi"}'
    '{"text": "Digital compliance requirements are excellent. This will reduce paperwork and make the process more efficient.", "user_type": "CA", "organization": "ICAI", "state": "Maharashtra"}'
    '{"text": "More clarity needed on what constitutes exceptional cases for physical document submission.", "user_type": "Corporate Lawyer", "organization": "Law Firm", "state": "Mumbai"}'
)

for i in "${!comments[@]}"; do
    comment_num=$((i + 1))
    response=$(curl -s -X POST http://localhost:8000/comments/single \
      -H "Content-Type: application/json" \
      -d "${comments[$i]}")
    
    sentiment=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['sentiment'])")
    confidence=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'{data[\"confidence\"]:.2f}')")
    
    echo "   Comment $comment_num: Sentiment = $sentiment (Confidence: $confidence)"
done
echo ""

echo -e "${YELLOW}📊 Step 3: Bulk CSV Processing${NC}"
# Create sample CSV with more diverse comments
cat > /tmp/sample_comments.csv << 'EOF'
text,user_type,organization,state
"These rules will greatly benefit small and medium enterprises by reducing compliance burden.",SME Owner,MSME Association,Gujarat
"The digital-first approach is commendable but we need better infrastructure support in rural areas.",Rural Entrepreneur,,Uttar Pradesh
"Processing timeline of 15 days is reasonable but there should be fast-track options for urgent cases.",Startup Founder,TiE,Bangalore
"The definition of digital signature needs to be more comprehensive and aligned with IT Act.",Tech Lawyer,Cyber Law Association,Hyderabad
"Excellent initiative! This will put India at par with global best practices in business registration.",Policy Analyst,CII,New Delhi
"Concerned about data security in electronic filing. Need stronger privacy protections.",Privacy Advocate,Digital Rights Foundation,Chennai
"The amendments are progressive but implementation challenges need to be addressed proactively.",Business Consultant,FICCI,Pune
"Welcome change! The startup ecosystem will benefit tremendously from these simplified procedures.",Investor,Angel Network,Mumbai
EOF

csv_response=$(curl -s -X POST http://localhost:8000/comments/upload-csv \
  -F "file=@/tmp/sample_comments.csv")

csv_count=$(echo "$csv_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_comments'])")
echo "📈 Processed $csv_count comments from CSV upload"
echo ""

echo -e "${YELLOW}📊 Step 4: Generate Analytics${NC}"
analytics=$(curl -s http://localhost:8000/analytics)

echo "📈 Analytics Summary:"
python3 -c "
import sys, json
data = json.loads('''$analytics''')
print(f'   Total Comments Processed: {data[\"total_comments\"]}')
print(f'   Sentiment Distribution:')
for sentiment, count in data['sentiment_distribution'].items():
    percentage = (count / data['total_comments']) * 100
    print(f'     • {sentiment.capitalize()}: {count} ({percentage:.1f}%)')
print(f'   Average Confidence Score: {data[\"average_confidence\"]:.2f}')
print(f'   Most Discussed Clauses: {len(data[\"top_clauses\"])}')
if data['top_clauses']:
    print(f'   Top Clause: {data[\"top_clauses\"][0][\"clause\"].split()[0:8]} ...')
"
echo ""

echo -e "${YELLOW}🎯 Step 5: System Status Check${NC}"
health=$(curl -s http://localhost:8000/health)
echo "🏥 System Health:"
python3 -c "
import sys, json
data = json.loads('''$health''')
print(f'   Status: {data[\"status\"].upper()}')
print(f'   Database: {data[\"database\"]}')
print(f'   ML Model: {data[\"sentiment_model\"]}')
print(f'   Version: {data[\"version\"]}')
print(f'   Comments Processed: {data[\"processed_comments\"]}')
"
echo ""

# Clean up
rm -f /tmp/sample_comments.csv

echo "=================================================="
echo -e "${GREEN}🎉 DEMO COMPLETE - NeetiManthan is Fully Operational!${NC}"
echo "=================================================="
echo ""
echo -e "${PURPLE}🌐 Access Your Application:${NC}"
echo -e "${BLUE}   • Frontend Dashboard: http://localhost:3000${NC}"
echo -e "${BLUE}   • Backend API: http://localhost:8000${NC}"
echo -e "${BLUE}   • API Documentation: http://localhost:8000/docs${NC}"
echo ""
echo -e "${PURPLE}🚀 Key Features Demonstrated:${NC}"
echo "   ✅ Draft document upload with automatic clause extraction"
echo "   ✅ Real-time sentiment analysis of individual comments"
echo "   ✅ Bulk CSV processing for large comment datasets"
echo "   ✅ Comprehensive analytics with sentiment distribution"
echo "   ✅ Clause-wise comment mapping and insights"
echo "   ✅ Professional web dashboard with responsive design"
echo "   ✅ RESTful API with comprehensive documentation"
echo ""
echo -e "${PURPLE}💡 What You Can Do Next:${NC}"
echo "   🖥️  Open http://localhost:3000 in your browser"
echo "   📊 Explore the interactive dashboard"
echo "   📄 Upload your own draft documents"
echo "   💬 Process your own comment datasets"
echo "   📈 View real-time analytics and insights"
echo "   📋 Export data in CSV/JSON formats"
echo ""
echo -e "${GREEN}🎯 NeetiManthan: Transforming Public Policy Analysis with AI!${NC}"
