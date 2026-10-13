"""
Utility functions for Discord bot interactions
"""
import asyncio
import logging
import discord
import aiohttp

log = logging.getLogger(__name__)

async def safe_edit(message, *, retries: int = 2, delay: float = 1.0, **kwargs) -> bool:
    """
    Edit một message Discord một cách an toàn.
    Tự động retry khi bị lỗi mạng tạm thời hoặc rate-limit.
    """
    for attempt in range(retries + 1):
        try:
            await message.edit(**kwargs)
            return True
        except (aiohttp.ClientOSError, aiohttp.ServerDisconnectedError, asyncio.TimeoutError):
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                log.warning("safe_edit: Mất kết nối sau %d lần thử, bỏ qua.", retries + 1)
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = getattr(e, 'retry_after', delay)
                await asyncio.sleep(retry_after)
                if attempt < retries:
                    continue
            elif e.status in (500, 502, 503, 504):
                if attempt < retries:
                    await asyncio.sleep(delay * (attempt + 1))
                    continue
            else:
                log.warning("safe_edit: HTTPException %d - %s", e.status, e.text)
        except Exception as e:
            log.warning("safe_edit: Lỗi không xác định: %s", e)
        break
    return False

async def safe_interaction_edit(interaction, *, retries: int = 2, delay: float = 1.0, **kwargs) -> bool:
    """
    Edit original interaction response an toàn.
    """
    for attempt in range(retries + 1):
        try:
            await interaction.edit_original_response(**kwargs)
            return True
        except (aiohttp.ClientOSError, aiohttp.ServerDisconnectedError, asyncio.TimeoutError):
            if attempt < retries:
                await asyncio.sleep(delay)
        except discord.HTTPException as e:
            if e.status == 429:
                retry_after = getattr(e, 'retry_after', delay)
                await asyncio.sleep(retry_after)
                if attempt < retries:
                    continue
        except Exception as e:
            log.warning("safe_interaction_edit error: %s", e)
        break
    return False
