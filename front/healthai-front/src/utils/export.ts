/**
 * Export utilities for dashboard data
 */

export interface ExportOptions {
  filename: string;
  format: 'csv' | 'json';
}

/**
 * Export data to CSV format
 */
export function exportAsCSV(data: any[], filename: string): void {
  if (!data || data.length === 0) {
    console.warn('No data to export');
    return;
  }

  // Get headers from first object
  const headers = Object.keys(data[0]);
  
  // Create CSV content
  const csvContent = [
    headers.join(','),
    ...data.map(row => 
      headers.map(header => {
        const value = row[header];
        // Escape quotes and handle commas
        if (value === null || value === undefined) return '';
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    )
  ].join('\n');

  downloadFile(csvContent, filename, 'text/csv;charset=utf-8;');
}

/**
 * Export data to JSON format
 */
export function exportAsJSON(data: any, filename: string): void {
  if (!data) {
    console.warn('No data to export');
    return;
  }

  const jsonString = JSON.stringify(data, null, 2);
  downloadFile(jsonString, filename, 'application/json;charset=utf-8;');
}

/**
 * Download file to user's computer
 */
function downloadFile(content: string, filename: string, contentType: string): void {
  const link = document.createElement('a');
  const blob = new Blob([content], { type: contentType });
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  URL.revokeObjectURL(url);
}

/**
 * Generate filename with timestamp
 */
export function generateFilename(prefix: string, format: 'csv' | 'json'): string {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
  return `${prefix}-${timestamp}.${format}`;
}

/**
 * Export analytics summary
 */
export function exportAnalyticsSummary(
  summary: any,
  period: { from: string; to: string },
  format: 'csv' | 'json' = 'json'
): void {
  const data = {
    exportDate: new Date().toISOString(),
    period,
    summary
  };

  if (format === 'json') {
    exportAsJSON(data, generateFilename('analytics-summary', 'json'));
  } else {
    // Convert to array format for CSV
    const csvData = [
      {
        'Metric': 'Export Date',
        'Value': data.exportDate
      },
      {
        'Metric': 'Period From',
        'Value': period.from
      },
      {
        'Metric': 'Period To',
        'Value': period.to
      },
      ...Object.entries(summary || {}).map(([key, value]) => ({
        'Metric': key,
        'Value': String(value)
      }))
    ];
    exportAsCSV(csvData, generateFilename('analytics-summary', 'csv'));
  }
}

/**
 * Export data quality report
 */
export function exportQualityReport(
  etlQuality: any,
  format: 'csv' | 'json' = 'json'
): void {
  if (format === 'json') {
    exportAsJSON(etlQuality, generateFilename('quality-report', 'json'));
  } else {
    // Convert completeness data to CSV format
    const csvData: Array<Record<string, string | number>> = [];
    
    if (etlQuality?.summary) {
      Object.entries(etlQuality.summary).forEach(([key, value]) => {
        csvData.push({
          'Category': 'Summary',
          'Metric': key,
          'Value': String(value)
        });
      });
    }

    if (etlQuality?.data_completeness) {
      Object.entries(etlQuality.data_completeness).forEach(([key, stats]: any) => {
        csvData.push({
          'Category': 'Completeness',
          'Metric': key,
          'Completeness %': String((stats.completeness_percent * 100).toFixed(2)),
          'Valid': stats.valid_count,
          'Total': stats.total_count
        });
      });
    }

    exportAsCSV(csvData, generateFilename('quality-report', 'csv'));
  }
}
