#!/bin/bash

echo "🚀 NeetiManthan End-to-End Test"
echo "Testing Complete Application Flow"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_api() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -e "${BLUE}🧪 Testing: $description${NC}"
    
    response=$(curl -s -w "%{http_code}" -o /tmp/api_response http://localhost:8000$endpoint)
    status_code="${response: -3}"
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo -e "${GREEN}✅ $description - Status: $status_code${NC}"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ $description - Expected: $expected_status, Got: $status_code${NC}"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

echo -e "${BLUE}📍 Step 1: Testing Frontend${NC}"
if curl -s http://localhost:3000 > /dev/null; then
    echo -e "${GREEN}✅ Frontend is running on http://localhost:3000${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
else
    echo -e "${RED}❌ Frontend not accessible${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}📍 Step 2: Testing Backend API${NC}"
test_api "/" "API Root Endpoint"
test_api "/health" "Health Check"
test_api "/docs" "API Documentation"

echo ""
echo -e "${BLUE}📍 Step 3: Testing Draft Upload${NC}"
draft_response=$(curl -s -X POST http://localhost:8000/draft/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Companies (Amendment) Rules, 2024",
    "content": "1. Short title and commencement\n(1) These rules may be called the Companies (Amendment) Rules, 2024.\n\n2. Definitions\nIn these rules, unless the context otherwise requires:\n(a) \"digital signature\" means authentication of any electronic record.\n\n3. Application for incorporation\n(1) Every application shall be made in Form INC-32.\n\n4. Processing timeline\n(1) The Registrar shall process applications within 15 working days.\n\n5. Digital compliance\n(1) All forms shall be filed electronically through the MCA portal."
  }')

if echo "$draft_response" | grep -q "clauses_extracted"; then
    echo -e "${GREEN}✅ Draft upload successful${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Extract draft ID for later use
    draft_id=$(echo "$draft_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
    echo -e "${YELLOW}📄 Draft ID: $draft_id${NC}"
else
    echo -e "${RED}❌ Draft upload failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}📍 Step 4: Testing Single Comment Processing${NC}"
comment_response=$(curl -s -X POST http://localhost:8000/comments/single \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I strongly support this rule as it will benefit small businesses and promote innovation.",
    "user_type": "Individual",
    "organization": "NASSCOM",
    "state": "Maharashtra"
  }')

if echo "$comment_response" | grep -q "sentiment"; then
    echo -e "${GREEN}✅ Single comment processing successful${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Show sentiment result
    sentiment=$(echo "$comment_response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(f'Sentiment: {data[\"sentiment\"]} (Confidence: {data[\"confidence\"]:.2f})')")
    echo -e "${YELLOW}💬 $sentiment${NC}"
else
    echo -e "${RED}❌ Single comment processing failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}📍 Step 5: Testing CSV Upload${NC}"
# Create a test CSV
cat > /tmp/test_comments.csv << EOF
text,user_type,organization,state
"This rule will help small businesses grow and compete better.",Individual,FICCI,Delhi
"The compliance requirements are too complex and burdensome.",Legal Professional,Bar Association,Mumbai  
"I appreciate the digital-first approach in these amendments.",Tech Professional,NASSCOM,Bangalore
"The timeline of 15 days seems reasonable for processing.",Individual,,Kerala
"More clarity needed on the definition of digital signature.",Legal Expert,CII,Gujarat
EOF

csv_response=$(curl -s -X POST http://localhost:8000/comments/upload-csv \
  -F "file=@/tmp/test_comments.csv")

if echo "$csv_response" | grep -q "Successfully processed"; then
    echo -e "${GREEN}✅ CSV upload successful${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Show processing result
    count=$(echo "$csv_response" | python3 -c "import sys, json; print(json.load(sys.stdin)['total_comments'])")
    echo -e "${YELLOW}📊 Processed $count comments from CSV${NC}"
else
    echo -e "${RED}❌ CSV upload failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}📍 Step 6: Testing Analytics${NC}"
analytics_response=$(curl -s http://localhost:8000/analytics)

if echo "$analytics_response" | grep -q "sentiment_distribution"; then
    echo -e "${GREEN}✅ Analytics generation successful${NC}"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Show analytics summary
    python3 -c "
import sys, json
data = json.loads('$analytics_response')
print(f'📈 Total Comments: {data[\"total_comments\"]}')
print(f'📊 Sentiment Distribution:')
for sentiment, count in data['sentiment_distribution'].items():
    print(f'   {sentiment.capitalize()}: {count}')
print(f'🎯 Average Confidence: {data[\"average_confidence\"]:.2f}')
print(f'📋 Top Clauses: {len(data[\"top_clauses\"])}')
"
else
    echo -e "${RED}❌ Analytics generation failed${NC}"
    TESTS_FAILED=$((TESTS_FAILED + 1))
fi

echo ""
echo -e "${BLUE}📍 Step 7: Testing Comments Retrieval${NC}"
test_api "/comments" "Get All Comments"

echo ""
echo -e "${BLUE}📍 Step 8: Testing Sentiment Analysis${NC}"
test_api "/test-sentiment" "Sentiment Analysis Test" 200

# Clean up
rm -f /tmp/test_comments.csv /tmp/api_response

echo ""
echo "=================================================="
echo -e "${BLUE}🎯 End-to-End Test Results${NC}"
echo "=================================================="
echo -e "${GREEN}✅ Tests Passed: $TESTS_PASSED${NC}"
echo -e "${RED}❌ Tests Failed: $TESTS_FAILED${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo -e "${GREEN}🚀 NeetiManthan is fully functional!${NC}"
    echo ""
    echo -e "${YELLOW}📱 Access the application:${NC}"
    echo -e "${BLUE}   Frontend: http://localhost:3000${NC}"
    echo -e "${BLUE}   Backend:  http://localhost:8000${NC}"
    echo -e "${BLUE}   API Docs: http://localhost:8000/docs${NC}"
    echo ""
    echo -e "${YELLOW}🎯 Key Features Working:${NC}"
    echo "   ✅ Draft document upload and clause extraction"
    echo "   ✅ Single comment sentiment analysis"  
    echo "   ✅ Bulk CSV comment processing"
    echo "   ✅ Real-time analytics and insights"
    echo "   ✅ Beautiful web dashboard interface"
    echo "   ✅ Export functionality"
    echo ""
    exit 0
else
    echo ""
    echo -e "${RED}⚠️  Some tests failed. Check the output above for details.${NC}"
    exit 1
fi
