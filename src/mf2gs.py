import download_history
import export_gspread
from my_logging import get_my_logger
logger = get_my_logger(__name__)


if __name__ == "__main__":
    logger.info(f"START SCRIPT {'='*10}")
    download_history.main()
    export_gspread.main()
    logger.info(f"END SCRIPT {'='*10}")