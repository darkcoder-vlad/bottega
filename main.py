#!/usr/bin/env python3
"""
БОТТЕГА квест - Telegram Bot для программы лояльности ресторана
Main entry point
"""

import asyncio
import sys
import os

# Add bottega_hub to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bottega_hub'))

from bot.dispatcher import start_bot


def main():
    """Main function"""
    print("=" * 50)
    print("БОТТЕГА квест - Loyalty Program Bot")
    print("=" * 50)
    print()
    
    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
