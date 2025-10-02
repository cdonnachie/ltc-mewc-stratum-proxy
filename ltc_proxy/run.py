import asyncio
from .config import Settings
from .logging_setup import setup_logging
from .state.template import TemplateState
from .state.updater import state_updater_loop, update_once
from .stratum.server import start_server
from .zmq.listener import TripleZMQListener


def run_with_settings(settings: Settings):
    logger = setup_logging(settings.verbose)

    # Determine mode based on configured chains
    modes = []
    if settings.aux_url and settings.aux_address:
        modes.append("MEWC")
    if settings.doge_url and settings.doge_address:
        modes.append("DOGE")

    if modes:
        mode = f"LTC+{'+'.join(modes)} AuxPoW"
    else:
        mode = "LTC only"

    logger.info("Mode: %s", mode)
    if settings.aux_url and settings.aux_address:
        logger.info("MEWC address: %s", settings.aux_address)
    if settings.doge_url and settings.doge_address:
        logger.info("DOGE address: %s", settings.doge_address)

    # Log ZMQ configuration
    if settings.enable_zmq:
        zmq_endpoints = [f"LTC: {settings.ltc_zmq_endpoint}"]
        if settings.aux_url:
            zmq_endpoints.append(f"MEWC: {settings.mewc_zmq_endpoint}")
        if settings.doge_url:
            zmq_endpoints.append(f"DOGE: {settings.doge_zmq_endpoint}")
        logger.info("ZMQ enabled - %s", ", ".join(zmq_endpoints))
    else:
        logger.info("ZMQ disabled - using polling only")

    state = TemplateState()

    async def main():
        from aiohttp import ClientSession

        async with ClientSession() as http:
            # ZMQ callbacks
            async def on_ltc_block(block_hash: str):
                logger.info("ZMQ: New LTC block %s, updating template", block_hash)
                try:
                    await update_once(state, settings, http, force_update=True)
                except Exception as e:
                    logger.error("Failed to update template on LTC block: %s", e)

            async def on_mewc_block(block_hash: str):
                logger.info("ZMQ: New MEWC block %s, refreshing aux job", block_hash)
                try:
                    from .consensus.auxpow import refresh_aux_job

                    await refresh_aux_job(
                        state,
                        http,
                        settings.aux_url,
                        settings.aux_address,
                        force_update=True,
                    )
                    # Update template with new aux job if successful
                    if state.aux_job:
                        await update_once(state, settings, http, force_update=False)
                except Exception as e:
                    logger.error("Failed to refresh aux job on MEWC block: %s", e)

            async def on_doge_block(block_hash: str):
                logger.info("ZMQ: New DOGE block %s, refreshing doge job", block_hash)
                try:
                    from .consensus.auxpow import refresh_doge_job

                    await refresh_doge_job(
                        state,
                        http,
                        settings.doge_url,
                        settings.doge_address,
                        force_update=True,
                    )
                    # Update template with new doge job if successful
                    if state.doge_job:
                        await update_once(state, settings, http, force_update=False)
                except Exception as e:
                    logger.error("Failed to refresh doge job on DOGE block: %s", e)

            # Create tasks
            tasks = []

            # Always start the state updater (now with reduced frequency when ZMQ is active)
            tasks.append(asyncio.create_task(state_updater_loop(state, settings)))

            # Start stratum server
            tasks.append(asyncio.create_task(start_server(state, settings)))

            # Start ZMQ listener if enabled
            if settings.enable_zmq:
                zmq_listener = TripleZMQListener(
                    ltc_endpoint=settings.ltc_zmq_endpoint,
                    mewc_endpoint=(
                        settings.mewc_zmq_endpoint if settings.aux_url else None
                    ),
                    doge_endpoint=(
                        settings.doge_zmq_endpoint if settings.doge_url else None
                    ),
                    on_ltc_block=on_ltc_block,
                    on_mewc_block=on_mewc_block if settings.aux_url else None,
                    on_doge_block=on_doge_block if settings.doge_url else None,
                )
                tasks.append(asyncio.create_task(zmq_listener.start()))

            # Wait for any task to complete or fail
            await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)

    asyncio.run(main())


def run_from_env():
    run_with_settings(Settings())
