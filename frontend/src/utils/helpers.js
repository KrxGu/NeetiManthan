import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO } from 'date-fns';

// Utility function to merge Tailwind classes
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// Format date strings
export function formatDate(dateString, formatStr = 'MMM dd, yyyy') {
  if (!dateString) return '';
  try {
    return format(parseISO(dateString), formatStr);
  } catch (error) {
    return dateString;
  }
}

// Format date with time
export function formatDateTime(dateString) {
  return formatDate(dateString, 'MMM dd, yyyy HH:mm');
}

// Get sentiment color class
export function getSentimentColor(sentiment) {
  switch (sentiment?.toLowerCase()) {
    case 'positive':
      return 'text-success-600 bg-success-50 border-success-200';
    case 'negative':
      return 'text-danger-600 bg-danger-50 border-danger-200';
    case 'neutral':
      return 'text-gray-600 bg-gray-50 border-gray-200';
    default:
      return 'text-gray-600 bg-gray-50 border-gray-200';
  }
}

// Get sentiment badge class
export function getSentimentBadge(sentiment) {
  switch (sentiment?.toLowerCase()) {
    case 'positive':
      return 'badge-success';
    case 'negative':
      return 'badge-danger';
    case 'neutral':
      return 'badge-gray';
    default:
      return 'badge-gray';
  }
}

// Get confidence level text and color
export function getConfidenceLevel(confidence) {
  const conf = parseFloat(confidence);
  if (conf >= 0.8) {
    return { text: 'High', color: 'text-success-600' };
  } else if (conf >= 0.6) {
    return { text: 'Medium', color: 'text-warning-600' };
  } else {
    return { text: 'Low', color: 'text-danger-600' };
  }
}

// Truncate text
export function truncateText(text, maxLength = 100) {
  if (!text || text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

// Format numbers with commas
export function formatNumber(num) {
  return new Intl.NumberFormat().format(num);
}

// Calculate percentage
export function calculatePercentage(value, total) {
  if (!total || total === 0) return 0;
  return Math.round((value / total) * 100);
}

// Debounce function
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Download data as JSON
export function downloadJSON(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Download data as CSV
export function downloadCSV(data, filename) {
  if (!data.length) return;
  
  const headers = Object.keys(data[0]);
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape commas and quotes in CSV
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Validate file type
export function validateFileType(file, allowedTypes) {
  return allowedTypes.includes(file.type);
}

// Validate file size (in MB)
export function validateFileSize(file, maxSizeMB) {
  const fileSizeMB = file.size / (1024 * 1024);
  return fileSizeMB <= maxSizeMB;
}

// Generate random ID
export function generateId() {
  return Math.random().toString(36).substr(2, 9);
}
