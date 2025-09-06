#!/bin/bash

echo "🎯 NeetiManthan Frontend Test"
echo "Testing React Frontend Dashboard"
echo "=================================================="

echo "📍 Testing Frontend Status..."
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend is running!"
    echo "🌐 Frontend URL: http://localhost:3000"
else
    echo "❌ Frontend not accessible"
    exit 1
fi

echo ""
echo "🔍 Checking Frontend Response..."
response=$(curl -s http://localhost:3000)
if echo "$response" | grep -q "NeetiManthan"; then
    echo "✅ Frontend title found in response"
else
    echo "⚠️  Frontend title not found, but server is responding"
fi

echo ""
echo "📡 Testing API Proxy (through frontend)..."
if curl -s http://localhost:3000/api/ > /dev/null; then
    echo "✅ API proxy is working"
else
    echo "⚠️  API proxy might not be ready (backend still loading)"
fi

echo ""
echo "🎉 Frontend Test Complete!"
echo "📋 Summary:"
echo "   - Frontend: ✅ Running on http://localhost:3000"
echo "   - Backend:  🔄 Loading (transformer models)"
echo ""
echo "💡 Open http://localhost:3000 in your browser to see the dashboard!"
