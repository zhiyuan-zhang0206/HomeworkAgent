from .timestamp import get_current_run_timestamp
from loguru import logger
from pathlib import Path

def configure_default_logger(log_dir=None, file_name=None, use_date_subdir=True, suffix:str=None):
    """Configure a default logger. Log file name is the timestamp for the current run.
    
    Args:
        log_dir (Path, optional): The directory to save the log file. Defaults to the current working directory.
        file_name (str, optional): The name of the log file. Defaults to the current timestamp.
        use_date_subdir (bool, optional): Whether to use the current date as a subdirectory. Defaults to False.
    """
    if log_dir is None:
        log_dir = Path('data') / 'logs'
    
    # use a default "latest.log" file, clear the file if it exists
    latest_log_file = log_dir / 'latest.log'
    if latest_log_file.exists():
        latest_log_file.unlink()
    logger.add(latest_log_file, encoding='utf-8')


    if use_date_subdir:
        date_subdir = get_current_run_timestamp().split('_')[0]
        log_dir = log_dir / date_subdir
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    if file_name is None and suffix is None:
        file_name = get_current_run_timestamp()
    elif file_name is None and suffix is not None:
        file_name = get_current_run_timestamp() + '_' + suffix
    elif file_name is not None and suffix is None:
        pass
    else:
        file_name = file_name + '_' + suffix
    file_name += '.log'
    log_file_path = log_dir / file_name
    
    logger.add(log_file_path, encoding='utf-8')
    logger.info(f"Logging to {log_file_path.absolute().as_posix()} and {latest_log_file.absolute().as_posix()}")
    return logger