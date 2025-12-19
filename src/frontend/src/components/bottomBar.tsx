import { Button, Card, Dropdown, DropdownProps, Option } from "@fluentui/react-components"
import React, { useState } from "react"
import { useNavigate } from "react-router-dom"

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
      onStartTranslating()

    }
  }
  
  return (
    <div className="bottom-bar bg-gray-800 flex items-center px-4 h-[10vh] shadow-lg border-t border-gray-200 fixed bottom-0 left-0 right-0">
      <Card
        style={{
          backgroundColor: "#FAFAFA",
          padding: "1rem",
          borderRadius: "0",
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          zIndex:1000,
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            width: "55%",
            justifyContent: "space-between",
            gap: "2rem",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "2rem",
              flexGrow: 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <label htmlFor="currentLanguage" className="text-sm text-gray-900">
                Translate from
              </label>
              <Dropdown
                id="currentLanguage"
                style={{ width: "150px" }}
                selectedOptions={selectedCurrentLanguage} 
                onOptionSelect={handleCurrentLanguageChange}
                defaultValue="Informix"
              >
                <Option value="Informix">Informix</Option>
              </Dropdown>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
              <label htmlFor="targetLanguage" className="text-sm text-gray-900">
                Translate to
              </label>
              <Dropdown
                id="targetLanguage"
                style={{ width: "150px" }}
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
            style={{
              display: "flex",
              alignItems: "center",
              gap: "1rem",
            }}
          >
            <Button
              disabled={uploadState === UploadState.IDLE}
              onClick={handleCancel}
              appearance="secondary"
              style={{
                minWidth: "80px",
              }}
            >
              Cancel
            </Button>
            <Button
              disabled={uploadState !== UploadState.COMPLETED}
              onClick={handleStartTranslating}
              appearance="primary"
              style={{
                minWidth: "120px",
              }}
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