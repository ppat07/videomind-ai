#!/usr/bin/env python3
"""
VideoMind AI: Cleanup Script for Stuck and Failed Jobs
Demonstrates the job management system in action.
"""
import sqlite3
import sys
from datetime import datetime, timedelta

def cleanup_stuck_jobs():
    """Clean up jobs stuck in downloading status for days."""
    conn = sqlite3.connect('videomind.db')
    
    print("🧹 VideoMind AI: Job Cleanup & Recovery")
    print("=" * 50)
    
    # First, show current state
    print("\n📊 BEFORE CLEANUP:")
    statuses = conn.execute('SELECT status, COUNT(*) FROM video_jobs GROUP BY status').fetchall()
    for status, count in statuses:
        print(f"  {status}: {count}")
    
    # Identify stuck downloads (3+ days old in downloading status)
    three_days_ago = (datetime.utcnow() - timedelta(days=3)).isoformat()
    stuck_downloads = conn.execute('''
        SELECT id, youtube_url, created_at 
        FROM video_jobs 
        WHERE status = "downloading" AND created_at < ?
    ''', (three_days_ago,)).fetchall()
    
    print(f"\n🔍 Found {len(stuck_downloads)} jobs stuck in downloading status for 3+ days")
    
    # Reset stuck downloads to failed with clear error message
    if stuck_downloads:
        print("\n🔄 Resetting stuck downloads to failed status...")
        for job_id, url, created_at in stuck_downloads:
            url_short = url[:50] + "..." if len(url) > 50 else url
            print(f"  Resetting: {job_id[:8]}... {url_short}")
            
            conn.execute('''
                UPDATE video_jobs 
                SET status = "failed", 
                    error_message = "Job cleanup: Reset from stuck downloading status (3+ days old)",
                    retry_count = COALESCE(retry_count, "0")
                WHERE id = ?
            ''', (job_id,))
    
    # Count failed jobs that haven't been retried
    failed_jobs = conn.execute('''
        SELECT COUNT(*) FROM video_jobs 
        WHERE status = "failed" 
        AND (retry_count IS NULL OR retry_count = "0" OR retry_count = "")
    ''').fetchone()[0]
    
    print(f"\n📋 Found {failed_jobs} failed jobs that haven't been retried yet")
    
    # Mark YouTube-blocked jobs as permanently failed (no retry)
    youtube_blocked = conn.execute('''
        UPDATE video_jobs 
        SET retry_count = "999",
            error_message = error_message || " [Auto-marked: YouTube blocking, no retry]"
        WHERE status = "failed" 
        AND error_message LIKE "%403 Forbidden%"
        AND (retry_count IS NULL OR retry_count != "999")
    ''')
    
    blocked_count = youtube_blocked.rowcount
    if blocked_count > 0:
        print(f"  Marked {blocked_count} YouTube-blocked jobs as permanently failed")
    
    # Mark Whisper API failures for retry (these might work now)
    whisper_failures = conn.execute('''
        UPDATE video_jobs 
        SET retry_count = "0",
            error_message = error_message || " [Ready for retry]"
        WHERE status = "failed" 
        AND error_message LIKE "%Whisper transcription failed%"
        AND (retry_count IS NULL OR retry_count = "")
    ''')
    
    whisper_count = whisper_failures.rowcount
    if whisper_count > 0:
        print(f"  Marked {whisper_count} Whisper API failures as ready for retry")
    
    # Mark FFmpeg failures for retry (might work with current fixes)
    ffmpeg_failures = conn.execute('''
        UPDATE video_jobs 
        SET retry_count = "0",
            error_message = error_message || " [Ready for retry - ffmpeg fixes applied]"
        WHERE status = "failed" 
        AND error_message LIKE "%Audio conversion failed%"
        AND (retry_count IS NULL OR retry_count = "")
    ''')
    
    ffmpeg_count = ffmpeg_failures.rowcount
    if ffmpeg_count > 0:
        print(f"  Marked {ffmpeg_count} FFmpeg failures as ready for retry")
    
    conn.commit()
    
    # Show final state
    print(f"\n📊 AFTER CLEANUP:")
    statuses = conn.execute('SELECT status, COUNT(*) FROM video_jobs GROUP BY status').fetchall()
    for status, count in statuses:
        print(f"  {status}: {count}")
    
    # Show retry-ready vs permanently failed breakdown
    print(f"\n🔄 FAILED JOB BREAKDOWN:")
    retry_ready = conn.execute('SELECT COUNT(*) FROM video_jobs WHERE status = "failed" AND retry_count = "0"').fetchone()[0]
    permanently_failed = conn.execute('SELECT COUNT(*) FROM video_jobs WHERE status = "failed" AND retry_count = "999"').fetchone()[0]
    other_failed = conn.execute('SELECT COUNT(*) FROM video_jobs WHERE status = "failed" AND retry_count NOT IN ("0", "999")').fetchone()[0]
    
    print(f"  Ready for retry: {retry_ready}")
    print(f"  Permanently failed (blocked): {permanently_failed}")
    print(f"  Other failed: {other_failed}")
    
    conn.close()
    
    return {
        "stuck_downloads_fixed": len(stuck_downloads),
        "youtube_blocked_marked": blocked_count,
        "whisper_retry_ready": whisper_count,
        "ffmpeg_retry_ready": ffmpeg_count,
        "total_retry_ready": retry_ready
    }

if __name__ == "__main__":
    results = cleanup_stuck_jobs()
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"📈 MEASURABLE IMPROVEMENTS:")
    print(f"  • Fixed {results['stuck_downloads_fixed']} stuck downloads")
    print(f"  • Categorized {results['youtube_blocked_marked']} permanently blocked jobs")
    print(f"  • Prepared {results['whisper_retry_ready']} Whisper failures for retry")
    print(f"  • Prepared {results['ffmpeg_retry_ready']} FFmpeg failures for retry")
    print(f"  • Total jobs ready for retry: {results['total_retry_ready']}")
    
    print(f"\n🚀 NEXT STEPS:")
    print(f"  1. Visit http://localhost:8000/jobs to see the new job management UI")
    print(f"  2. Use 'Retry Failed Jobs' button to retry the {results['total_retry_ready']} eligible jobs")
    print(f"  3. Monitor system health with the new dashboard")
    print(f"  4. Failed jobs now properly categorized for better debugging")