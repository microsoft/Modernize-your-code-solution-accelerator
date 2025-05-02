import { Button, Card, Dropdown, DropdownProps, Option } from "@fluentui/react-components"
import React, { useState } from "react"
import { useNavigate } from "react-router-dom"
import { updateBatchSummary } from "../../store/modernizationSlice"
import { useDispatch } from "react-redux"
import "./bottomBar.scss"

// Define possible upload states
const UploadState = {
  IDLE: "IDLE",
  UPLOADING: "UPLOADING",
  COMPLETED: "COMPLETED",
}

type UploadStateType = keyof typeof UploadState

interface BottomBarProps {
  uploadState: UploadStateType
  onCancel: () => void
  onStartTranslating: () => void
  selectedTargetLanguage: string[];
  selectedCurrentLanguage: string[];
  onTargetLanguageChange: (targetLanguage: string[]) => void;
  onCurrentLanguageChange: (currentLanguage: string[]) => void;
}

const BottomBar: React.FC<BottomBarProps> = ({ uploadState = UploadState.IDLE, onCancel, onStartTranslating, selectedTargetLanguage, selectedCurrentLanguage, onTargetLanguageChange, onCurrentLanguageChange }) => {
  const dispatch = useDispatch()
  const handleCancel = () => {
    if (onCancel) {
      onCancel()
    }
  }

  const handleCurrentLanguageChange: DropdownProps["onOptionSelect"] = (ev, data) => {
    if (data.optionValue) {
      onCurrentLanguageChange([data.optionValue]);
    }
  };

  const handleTargetLanguageChange: DropdownProps["onOptionSelect"] = (ev, data) => {
    if (data.optionValue) {
      onTargetLanguageChange([data.optionValue]);
    }
  };

  const handleStartTranslating = () => {
    if (uploadState === UploadState.COMPLETED) {
      dispatch(updateBatchSummary({
        batch_id: "",
        upload_id: "",
        date_created: "",
        total_files: 0,
        completed_files: 0,
        error_count: 0,
        status: "",
        warning_count: 0,
        hasFiles: 0,
        files: [] as {
          file_id: string;
          name: string;
          status: string;
          error_count: number;
          warning_count: number;
          file_logs: any[];
          content?: string;
          translated_content?: string;
        }[],
      }));
      onStartTranslating()
    }
  }
  
  return (
    <div className="bottom-bar bg-gray-800 flex items-center px-4 h-[10vh] shadow-lg border-t border-gray-200 fixed bottom-0 left-0 right-0">
      <Card
        className="cardContainer"
      >
        <div
          className="cardContainer2"
        >
          <div
            className="cardHeader"
          >
            <div className="cardLabel">
              <label htmlFor="currentLanguage" className="text-sm text-gray-900">
                Translate from
              </label>
              <Dropdown
                id="currentLanguage"
                className="width_150"
                selectedOptions={selectedCurrentLanguage} 
                onOptionSelect={handleCurrentLanguageChange}
                defaultValue="Informix"
              >
                <Option value="Informix">Informix</Option>
              </Dropdown>
            </div>
            <div className="cardLabel">
              <label htmlFor="targetLanguage" className="text-sm text-gray-900">
                Translate to
              </label>
              <Dropdown
                id="targetLanguage"
                className="width_150"
                selectedOptions={selectedTargetLanguage} // Controlled value, ensures dropdown value syncs with state
                onOptionSelect={handleTargetLanguageChange} // Correct event handler for value change
                defaultValue="T-SQL"
                //defaultSelectedOptions={selectedLanguage}
              >
                <Option value="T-SQL">T-SQL</Option>

              </Dropdown>
            </div>  
          </div>
          <div
            className="buttonContainer"
          >
            <Button
              disabled={uploadState === UploadState.IDLE}
              onClick={handleCancel}
              appearance="secondary"
              className="minWidth_80"
            >
              Cancel
            </Button>
            <Button
              disabled={uploadState !== UploadState.COMPLETED}
              onClick={handleStartTranslating}
              appearance="primary"
              className="minWidth_120"
            >
              Start translating
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default BottomBar;